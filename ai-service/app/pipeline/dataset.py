from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings
from app.pipeline.validator import PipelineValidator


def build_labels() -> Dict[str, Any]:
    """Generates real PR outcome labels."""
    script_path = settings.ROOT_DIR / "scripts" / "build_real_labels.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    runpy.run_path(str(script_path), run_name="__main__")
    return {"status": "SUCCESS", "stage": "labeling"}


def build_features() -> Dict[str, Any]:
    """Extracts features for labeled PRs."""
    script_path = settings.ROOT_DIR / "scripts" / "build_real_feature_dataset.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    runpy.run_path(str(script_path), run_name="__main__")
    return {"status": "SUCCESS", "stage": "features"}


def prepare_splits() -> Dict[str, Any]:
    """Generates repository-isolated train/validation/test splits."""
    script_path = settings.ROOT_DIR / "scripts" / "prepare_real_dataset_split.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    runpy.run_path(str(script_path), run_name="__main__")
    return {"status": "SUCCESS", "stage": "splits"}


def freeze_dataset() -> Dict[str, Any]:
    """Computes SHA-256 manifests to lock the dataset version."""
    script_path = settings.ROOT_DIR / "scripts" / "freeze_real_dataset.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    runpy.run_path(str(script_path), run_name="__main__")
    return {"status": "SUCCESS", "stage": "freeze"}


def run_dataset_pipeline(
    split: bool = True,
    freeze: bool = True,
) -> Dict[str, Any]:
    """Executes the full dataset curation sequence."""
    build_labels()
    build_features()
    if split:
        prepare_splits()
    if freeze:
        freeze_dataset()

    validator = PipelineValidator()
    val_res = validator.validate_dataset_splits()
    return {
        "status": "SUCCESS",
        "dataset_version": settings.DATASET_VERSION,
        "is_valid": val_res.is_valid,
        "details": val_res.details,
    }
