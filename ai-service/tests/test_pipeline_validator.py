from pathlib import Path
from app.pipeline.validator import PipelineValidator, compute_sha256
from app.core.config import settings


def test_validator_detects_current_valid_production_state():
    validator = PipelineValidator()
    results = validator.validate_all()

    # All current states in data/real should pass validation
    assert results["raw_data"].is_valid, f"Raw data invalid: {results['raw_data'].errors}"
    assert results["splits"].is_valid, f"Splits invalid: {results['splits'].errors}"
    assert results["features"].is_valid, f"Features invalid: {results['features'].errors}"
    assert results["trained_model"].is_valid, f"Trained model invalid: {results['trained_model'].errors}"
    assert results["production_artifact"].is_valid, f"Production artifact invalid: {results['production_artifact'].errors}"


def test_is_ready_for_training_and_promotion():
    validator = PipelineValidator()
    ready_train, train_errs = validator.is_ready_for_training()
    assert ready_train is True
    assert len(train_errs) == 0

    ready_promote, promote_errs = validator.is_ready_for_promotion("2.0.0")
    assert ready_promote is True
    assert len(promote_errs) == 0


def test_validator_fails_gracefully_on_missing_version(tmp_path):
    validator = PipelineValidator(root_dir=tmp_path)
    res = validator.validate_trained_model("9.9.9")
    assert res.is_valid is False
    assert len(res.errors) > 0


def test_validator_detects_tampered_stale_split_hash(tmp_path):
    import json
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
    (manifests_dir / "real_dataset_split_manifest.json").write_text(json.dumps(split_manifest), encoding="utf-8")

    validator = PipelineValidator(root_dir=tmp_path)
    res = validator.validate_dataset_splits()
    assert res.is_valid is False
    assert any("Stale dataset split: train.jsonl hash mismatch" in err for err in res.errors)

