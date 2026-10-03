from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings
from app.pipeline.validator import PipelineValidator


def promote_model(version: Optional[str] = None) -> Dict[str, Any]:
    """
    Validates model readiness and promotes trained model to production artifacts.
    """
    v = version or settings.MODEL_VERSION
    import os
    os.environ["MODEL_VERSION"] = v
    validator = PipelineValidator()

    # Pre-flight check
    ready, errors = validator.is_ready_for_promotion(v)
    if not ready:
        raise RuntimeError(
            f"Pre-flight promotion validation failed for model {v}:\n"
            + "\n".join(f" - {err}" for err in errors)
        )

    # Execute promote script
    script_path = settings.ROOT_DIR / "scripts" / "promote_real_model.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Promotion script not found: {script_path}")

    import runpy

    res = runpy.run_path(str(script_path), run_name="__main__")

    # Post-flight verification
    post_res = validator.validate_production_artifact(v)
    if not post_res.is_valid:
        raise RuntimeError(
            f"Post-promotion verification failed:\n"
            + "\n".join(f" - {err}" for err in post_res.errors)
        )

    return {
        "status": "SUCCESS",
        "model_version": v,
        "artifact_path": str(settings.production_model_path),
        "metadata_path": str(settings.production_metadata_path),
        "sha256": post_res.details.get("model_sha256"),
    }
