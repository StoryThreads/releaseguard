from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings
from app.pipeline.validator import PipelineValidator


def evaluate_models(version: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates trained model existence and runs the evaluation suite.
    """
    v = version or settings.MODEL_VERSION
    import os
    os.environ["MODEL_VERSION"] = v
    validator = PipelineValidator()

    # Pre-flight check
    model_res = validator.validate_trained_model(v)
    if not model_res.is_valid:
        raise RuntimeError(
            f"Pre-flight evaluation validation failed: Model {v} is not trained.\n"
            + "\n".join(f" - {err}" for err in model_res.errors)
        )

    script_path = settings.ROOT_DIR / "scripts" / "evaluate_real_models.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Evaluation script not found: {script_path}")

    res = runpy.run_path(str(script_path), run_name="__main__")

    # Post-flight verification
    post_res = validator.validate_evaluation(v)
    if not post_res.is_valid:
        raise RuntimeError(
            f"Post-evaluation validation failed:\n"
            + "\n".join(f" - {err}" for err in post_res.errors)
        )

    return {
        "status": "SUCCESS",
        "model_version": v,
        "details": post_res.details,
    }
