from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings
from app.pipeline.validator import PipelineValidator


def collect_prs(limit: Optional[int] = None) -> Dict[str, Any]:
    """Collects PR list, metadata, files, issues, and defect signals."""
    import os

    if limit is not None:
        os.environ["COLLECT_LIMIT"] = str(limit)

    script_path = settings.ROOT_DIR / "scripts" / "collect_real_prs.py"
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    runpy.run_path(str(script_path), run_name="__main__")

    validator = PipelineValidator()
    raw_res = validator.validate_raw_data()
    return {
        "status": "SUCCESS",
        "stage": "collection",
        "is_valid": raw_res.is_valid,
        "details": raw_res.details,
    }
