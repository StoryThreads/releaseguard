from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings
from app.pipeline.validator import PipelineValidator


def train_models(version: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates dataset splits and trains the real-data models.
    """
    v = version or settings.MODEL_VERSION
    import os
    os.environ["MODEL_VERSION"] = v
    validator = PipelineValidator()

    # Pre-flight check
    ready, errors = validator.is_ready_for_training()
    if not ready:
        raise RuntimeError(
            f"Pre-flight training validation failed:\n"
            + "\n".join(f" - {err}" for err in errors)
        )

    script_path = settings.ROOT_DIR / "scripts" / "train_real_models.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Training script not found: {script_path}")

    res = runpy.run_path(str(script_path), run_name="__main__")

    # Post-flight verification
    post_res = validator.validate_trained_model(v)
    if not post_res.is_valid:
        raise RuntimeError(
            f"Post-training validation failed:\n"
            + "\n".join(f" - {err}" for err in post_res.errors)
        )

    return {
        "status": "SUCCESS",
        "model_version": v,
        "details": post_res.details,
    }
