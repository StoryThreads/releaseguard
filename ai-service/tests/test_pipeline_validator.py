import json
from pathlib import Path
import pytest
from app.pipeline.validator import PipelineValidator, compute_sha256
from app.core.config import settings


@pytest.fixture
def mock_pipeline_dir(tmp_path):
    root = tmp_path / "mock_root"
    real_dir = root / "data" / "real"
    raw_dir = real_dir / "raw" / "repo1" / "pull_requests"
    splits_dir = real_dir / "splits"
    features_dir = real_dir / "features"
    manifests_dir = real_dir / "manifests"
    models_dir = real_dir / "models" / "2.0.0"
    eval_dir = real_dir / "evaluation" / "2.0.0"
    prod_dir = root / "artifacts" / "models" / "xgboost" / "2.0.0"

    raw_dir.mkdir(parents=True)
    splits_dir.mkdir(parents=True)
    features_dir.mkdir(parents=True)
    manifests_dir.mkdir(parents=True)
    models_dir.mkdir(parents=True)
    eval_dir.mkdir(parents=True)
    prod_dir.mkdir(parents=True)

    # Raw
    (manifests_dir / "pr_collection_manifest.json").write_text("{}", encoding="utf-8")

    # Splits
    (splits_dir / "train.jsonl").write_text('{"train": 1}\n', encoding="utf-8")
    (splits_dir / "validation.jsonl").write_text('{"val": 1}\n', encoding="utf-8")
    (splits_dir / "test.jsonl").write_text('{"test": 1}\n', encoding="utf-8")
    (manifests_dir / "dataset_freeze_manifest.json").write_text("{}", encoding="utf-8")

    split_manifest = {
        "output_sha256": {
            "train": compute_sha256(splits_dir / "train.jsonl"),
            "validation": compute_sha256(splits_dir / "validation.jsonl"),
            "test": compute_sha256(splits_dir / "test.jsonl"),
        }
    }
    (manifests_dir / "real_dataset_split_manifest.json").write_text(
        json.dumps(split_manifest), encoding="utf-8"
    )

    # Features
    (features_dir / "real_feature_dataset.jsonl").write_text(
        '{"features": []}\n', encoding="utf-8"
    )
    feat_manifest = {
        "hashes": {
            "feature_dataset_sha256": compute_sha256(
                features_dir / "real_feature_dataset.jsonl"
            )
        }
    }
    (manifests_dir / "real_feature_dataset_manifest.json").write_text(
        json.dumps(feat_manifest), encoding="utf-8"
    )

    # Models & Evaluation
    (models_dir / "xgboost.joblib").write_bytes(b"dummy_model")
    (models_dir / "model_metadata.json").write_text(
        json.dumps({"model_name": "xgboost", "model_version": "2.0.0"}),
        encoding="utf-8",
    )
    (eval_dir / "evaluation_report.json").write_text(
        json.dumps({"f1": 0.95}), encoding="utf-8"
    )

    # Production Artifact
    (prod_dir / "model.joblib").write_bytes(b"dummy_prod_model")
    (prod_dir / "metadata.json").write_text(
        json.dumps({"model_version": "2.0.0"}), encoding="utf-8"
    )

    return root


def test_validator_detects_committed_production_artifact():
    validator = PipelineValidator()
    result = validator.validate_production_artifact("2.0.0")
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validator_full_pipeline_validation_with_mock_state(mock_pipeline_dir):
    validator = PipelineValidator(root_dir=mock_pipeline_dir)
    results = validator.validate_all("2.0.0")

    assert results["raw_data"].is_valid, results["raw_data"].errors
    assert results["splits"].is_valid, results["splits"].errors
    assert results["features"].is_valid, results["features"].errors
    assert results["trained_model"].is_valid, results["trained_model"].errors
    assert results["evaluation"].is_valid, results["evaluation"].errors
    assert results["production_artifact"].is_valid, results["production_artifact"].errors

    ready_train, train_errs = validator.is_ready_for_training()
    assert ready_train is True
    assert len(train_errs) == 0

    ready_promote, promote_errs = validator.is_ready_for_promotion("2.0.0")
    assert ready_promote is True
    assert len(promote_errs) == 0


@pytest.mark.skipif(
    not (settings.DATA_DIR / "splits" / "train.jsonl").exists(),
    reason="Local real dataset not present in CI (gitignored)",
)
def test_validator_detects_local_dataset_when_present():
    validator = PipelineValidator()
    results = validator.validate_all()
    assert results["raw_data"].is_valid
    assert results["splits"].is_valid
    assert results["features"].is_valid
    assert results["trained_model"].is_valid
    assert results["production_artifact"].is_valid


def test_validator_fails_gracefully_on_missing_version(tmp_path):
    validator = PipelineValidator(root_dir=tmp_path)
    res = validator.validate_trained_model("9.9.9")
    assert res.is_valid is False
    assert len(res.errors) > 0


def test_validator_detects_tampered_stale_split_hash(tmp_path):
    # Setup mock structure with manifest expecting hash A but file having hash B
    real_dir = tmp_path / "data" / "real"
    splits_dir = real_dir / "splits"
    manifests_dir = real_dir / "manifests"
    splits_dir.mkdir(parents=True)
    manifests_dir.mkdir(parents=True)

    (splits_dir / "train.jsonl").write_text('{"tampered": true}', encoding="utf-8")
    (splits_dir / "validation.jsonl").write_text('{"ok": true}', encoding="utf-8")
    (splits_dir / "test.jsonl").write_text('{"ok": true}', encoding="utf-8")
    (manifests_dir / "dataset_freeze_manifest.json").write_text('{}', encoding="utf-8")

    split_manifest = {
        "output_sha256": {
            "train": "expected-hash-which-wont-match",
            "validation": compute_sha256(splits_dir / "validation.jsonl"),
            "test": compute_sha256(splits_dir / "test.jsonl"),
        }
    }
    (manifests_dir / "real_dataset_split_manifest.json").write_text(
        json.dumps(split_manifest), encoding="utf-8"
    )

    validator = PipelineValidator(root_dir=tmp_path)
    res = validator.validate_dataset_splits()
    assert res.is_valid is False
    assert any("Stale dataset split: train.jsonl hash mismatch" in err for err in res.errors)


