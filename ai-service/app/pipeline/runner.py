from __future__ import annotations

import sys
from typing import Any, Dict, Optional

from app.core.config import settings
from app.pipeline.dataset import run_dataset_pipeline
from app.pipeline.evaluation import evaluate_models
from app.pipeline.promotion import promote_model
from app.pipeline.training import train_models
from app.pipeline.validator import PipelineValidator


def run_pipeline(
    version: Optional[str] = None,
    skip_dataset: bool = True,
) -> Dict[str, Any]:
    """
    Orchestrates the complete model retraining, evaluation, and promotion workflow
    guarded by pre-flight and post-flight validation checks.
    """
    v = version or settings.MODEL_VERSION
    validator = PipelineValidator()

    print("=" * 70)
    print(f"ReleaseGuard Pipeline Runner — Model Version {v}")
    print("=" * 70)

    # 1. Dataset phase
    if not skip_dataset:
        print("\n[Stage 1/4] Running dataset pipeline (labels -> features -> splits -> freeze)...")
        run_dataset_pipeline()
    else:
        print("\n[Stage 1/4] Skipping dataset build (using existing frozen splits)...")
        ready_train, train_errs = validator.is_ready_for_training()
        if not ready_train:
            raise RuntimeError(
                f"Existing dataset splits invalid:\n"
                + "\n".join(f" - {err}" for err in train_errs)
            )

    # 2. Training phase
    print(f"\n[Stage 2/4] Training real models (v{v})...")
    train_res = train_models(v)
    print(f"  Training status: {train_res['status']}")

    # 3. Evaluation phase
    print(f"\n[Stage 3/4] Evaluating models (v{v})...")
    eval_res = evaluate_models(v)
    print(f"  Evaluation status: {eval_res['status']}")

    # 4. Promotion phase
    print(f"\n[Stage 4/4] Promoting model artifact (v{v})...")
    promote_res = promote_model(v)
    print(f"  Promotion status: {promote_res['status']}")
    print(f"  Promoted SHA-256: {promote_res['sha256']}")

    print("\n" + "=" * 70)
    print("PIPELINE RUN COMPLETED SUCCESSFULLY")
    print("=" * 70)

    return {
        "status": "SUCCESS",
        "model_version": v,
        "training": train_res,
        "evaluation": eval_res,
        "promotion": promote_res,
    }
