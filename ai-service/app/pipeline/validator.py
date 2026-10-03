from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class ValidationResult:
    stage: str
    is_valid: bool
    version: str
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class PipelineValidator:
    """
    Validates pipeline state before stage transitions to prevent:
    - Training against stale/missing datasets.
    - Evaluating on un-split data.
    - Promoting un-evaluated or mismatched model artifacts.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root_dir = root_dir or settings.ROOT_DIR
        self.real_data_dir = self.root_dir / "data" / "real"
        self.artifacts_dir = self.root_dir / "artifacts"

    def validate_raw_data(self) -> ValidationResult:
        stage = "raw_data"
        errors: List[str] = []
        details: Dict[str, Any] = {}

        raw_dir = self.real_data_dir / "raw"
        if not raw_dir.exists():
            errors.append(f"Raw data directory missing: {raw_dir}")
        else:
            pr_dirs = [p for p in raw_dir.glob("**/pull_requests") if p.is_dir()]
            details["raw_repo_dirs_found"] = len(pr_dirs)
            if not pr_dirs:
                errors.append("No collected PR directories found in data/real/raw/")

        manifest = self.real_data_dir / "manifests" / "pr_collection_manifest.json"
        if not manifest.exists():
            errors.append(f"PR collection manifest missing: {manifest}")
        else:
            details["pr_collection_manifest"] = manifest.name

        return ValidationResult(
            stage=stage,
            is_valid=len(errors) == 0,
            version=settings.DATASET_VERSION,
            details=details,
            errors=errors,
        )

    def validate_dataset_splits(self, version: Optional[str] = None) -> ValidationResult:
        stage = "dataset_splits"
        v = version or settings.DATASET_VERSION
        errors: List[str] = []
        details: Dict[str, Any] = {}

        splits_dir = self.real_data_dir / "splits"
        for split_name in ("train.jsonl", "validation.jsonl", "test.jsonl"):
            split_file = splits_dir / split_name
            if not split_file.exists():
                errors.append(f"Split file missing: {split_file}")
            elif split_file.stat().st_size == 0:
                errors.append(f"Split file is empty: {split_file}")
            else:
                details[split_name] = f"{split_file.stat().st_size} bytes"

        freeze_manifest = self.real_data_dir / "manifests" / "dataset_freeze_manifest.json"
        if not freeze_manifest.exists():
            errors.append(f"Dataset freeze manifest missing: {freeze_manifest}")
        else:
            details["freeze_manifest"] = freeze_manifest.name

        # Cryptographic integrity check against real_dataset_split_manifest.json
        split_manifest = self.real_data_dir / "manifests" / "real_dataset_split_manifest.json"
        if split_manifest.exists():
            try:
                split_manifest_data = json.loads(split_manifest.read_text(encoding="utf-8"))
                output_hashes = split_manifest_data.get("output_sha256", {})
                for split_key in ("train", "validation", "test"):
                    expected_sha = output_hashes.get(split_key)
                    file_path = splits_dir / f"{split_key}.jsonl"
                    if file_path.exists() and expected_sha:
                        actual_sha = compute_sha256(file_path)
                        if actual_sha != expected_sha:
                            errors.append(
                                f"Stale dataset split: {split_key}.jsonl hash mismatch! "
                                f"Found {actual_sha}, manifest expects {expected_sha}"
                            )
                        else:
                            details[f"{split_key}_hash_verified"] = True
            except Exception as e:
                errors.append(f"Failed to parse split manifest: {e}")

        return ValidationResult(
            stage=stage,
            is_valid=len(errors) == 0,
            version=v,
            details=details,
            errors=errors,
        )

    def validate_features(self, version: Optional[str] = None) -> ValidationResult:
        stage = "features"
        v = version or settings.FEATURE_VERSION
        errors: List[str] = []
        details: Dict[str, Any] = {}

        feature_file = self.real_data_dir / "features" / "real_feature_dataset.jsonl"
        if not feature_file.exists():
            errors.append(f"Feature dataset file missing: {feature_file}")
        elif feature_file.stat().st_size == 0:
            errors.append(f"Feature dataset file is empty: {feature_file}")
        else:
            details["feature_dataset_size_bytes"] = feature_file.stat().st_size

        feature_manifest = self.real_data_dir / "manifests" / "real_feature_dataset_manifest.json"
        if not feature_manifest.exists():
            errors.append(f"Feature dataset manifest missing: {feature_manifest}")
        else:
            details["feature_manifest"] = feature_manifest.name
            try:
                fm_data = json.loads(feature_manifest.read_text(encoding="utf-8"))
                expected_sha = fm_data.get("hashes", {}).get("feature_dataset_sha256")
                if feature_file.exists() and expected_sha:
                    actual_sha = compute_sha256(feature_file)
                    if actual_sha != expected_sha:
                        errors.append(
                            f"Stale feature dataset: hash mismatch! "
                            f"Found {actual_sha}, manifest expects {expected_sha}"
                        )
                    else:
                        details["feature_hash_verified"] = True
            except Exception as e:
                errors.append(f"Failed to parse feature manifest: {e}")

        return ValidationResult(
            stage=stage,
            is_valid=len(errors) == 0,
            version=v,
            details=details,
            errors=errors,
        )

    def validate_trained_model(self, version: Optional[str] = None) -> ValidationResult:
        stage = "trained_model"
        v = version or settings.MODEL_VERSION
        errors: List[str] = []
        details: Dict[str, Any] = {}

        model_dir = self.real_data_dir / "models" / v
        model_file = model_dir / "xgboost.joblib"
        metadata_file = model_dir / "model_metadata.json"

        if not model_file.exists():
            errors.append(f"Trained model artifact missing: {model_file}")
        else:
            details["model_artifact_size_bytes"] = model_file.stat().st_size

        if not metadata_file.exists():
            errors.append(f"Model metadata missing: {metadata_file}")
        else:
            try:
                meta = json.loads(metadata_file.read_text(encoding="utf-8"))
                details["model_name"] = meta.get("model_name")
                details["meta_version"] = meta.get("model_version")
                if str(meta.get("model_version")) != str(v):
                    errors.append(
                        f"Metadata model_version ({meta.get('model_version')}) does not match expected ({v})"
                    )
            except Exception as e:
                errors.append(f"Failed to parse metadata JSON: {e}")

        return ValidationResult(
            stage=stage,
            is_valid=len(errors) == 0,
            version=v,
            details=details,
            errors=errors,
        )

    def validate_evaluation(self, version: Optional[str] = None) -> ValidationResult:
        stage = "evaluation"
        v = version or settings.MODEL_VERSION
        errors: List[str] = []
        details: Dict[str, Any] = {}

        eval_file = self.real_data_dir / "models" / v / "evaluation.json"
        eval_report = self.real_data_dir / "evaluation" / v / "evaluation_report.json"

        if not eval_file.exists() and not eval_report.exists():
            errors.append(f"Evaluation report missing for model {v}")
        else:
            active_eval = eval_file if eval_file.exists() else eval_report
            details["evaluation_file"] = str(active_eval)
            try:
                data = json.loads(active_eval.read_text(encoding="utf-8"))
                details["has_metrics"] = bool(data)
            except Exception as e:
                errors.append(f"Failed to parse evaluation JSON: {e}")

        return ValidationResult(
            stage=stage,
            is_valid=len(errors) == 0,
            version=v,
            details=details,
            errors=errors,
        )

    def validate_production_artifact(self, version: Optional[str] = None) -> ValidationResult:
        stage = "production_artifact"
        v = version or settings.MODEL_VERSION
        errors: List[str] = []
        details: Dict[str, Any] = {}

        prod_dir = self.artifacts_dir / "models" / "xgboost" / v
        prod_model = prod_dir / "model.joblib"
        prod_meta = prod_dir / "metadata.json"
        manifest_file = self.real_data_dir / "manifests" / "production_model_promotion_manifest.json"

        if not prod_model.exists():
            errors.append(f"Production model artifact missing: {prod_model}")
        else:
            sha = compute_sha256(prod_model)
            details["model_sha256"] = sha

        if not prod_meta.exists():
            errors.append(f"Production metadata missing: {prod_meta}")

        if manifest_file.exists():
            try:
                manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
                expected_sha = manifest_data.get("production_artifact_sha256")
                if prod_model.exists() and expected_sha and sha != expected_sha:
                    errors.append(
                        f"Artifact SHA-256 mismatch! Found {sha}, manifest expects {expected_sha}"
                    )
                else:
                    details["manifest_sha_verified"] = True
            except Exception as e:
                errors.append(f"Failed to parse promotion manifest: {e}")
        else:
            details["manifest_sha_verified"] = False

        return ValidationResult(
            stage=stage,
            is_valid=len(errors) == 0,
            version=v,
            details=details,
            errors=errors,
        )

    def validate_all(self, model_version: Optional[str] = None) -> Dict[str, ValidationResult]:
        v = model_version or settings.MODEL_VERSION
        results = {
            "raw_data": self.validate_raw_data(),
            "features": self.validate_features(),
            "splits": self.validate_dataset_splits(),
            "trained_model": self.validate_trained_model(v),
            "evaluation": self.validate_evaluation(v),
            "production_artifact": self.validate_production_artifact(v),
        }
        return results

    def is_ready_for_training(self) -> tuple[bool, List[str]]:
        splits_res = self.validate_dataset_splits()
        feat_res = self.validate_features()
        errors = splits_res.errors + feat_res.errors
        return len(errors) == 0, errors

    def is_ready_for_promotion(self, model_version: Optional[str] = None) -> tuple[bool, List[str]]:
        v = model_version or settings.MODEL_VERSION
        model_res = self.validate_trained_model(v)
        eval_res = self.validate_evaluation(v)
        errors = model_res.errors + eval_res.errors
        return len(errors) == 0, errors
