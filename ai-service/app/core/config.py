from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Central configuration for ReleaseGuard AI Service and ML Pipelines."""

    # Service & Engine Versions
    SERVICE_VERSION: str = os.getenv("SERVICE_VERSION", "0.5.8")
    MODEL_VERSION: str = os.getenv("MODEL_VERSION", "2.0.0")
    FEATURE_VERSION: str = os.getenv("FEATURE_VERSION", "1.0.0")
    DATASET_VERSION: str = os.getenv("DATASET_VERSION", "2.0.0")

    # Network / Server Configuration
    HOST: str = os.getenv("AI_SERVICE_HOST", os.getenv("HOST", "0.0.0.0"))
    PORT: int = int(os.getenv("AI_SERVICE_PORT", os.getenv("PORT", "8000")))

    # Base Directories
    ROOT_DIR: Path = SERVICE_ROOT
    ARTIFACTS_DIR: Path = SERVICE_ROOT / "artifacts"
    DATA_DIR: Path = SERVICE_ROOT / "data"
    REAL_DATA_DIR: Path = DATA_DIR / "real"
    REAL_RAW_DIR: Path = REAL_DATA_DIR / "raw"
    REAL_LABELED_DIR: Path = REAL_DATA_DIR / "labeled"
    REAL_FEATURES_DIR: Path = REAL_DATA_DIR / "features"
    REAL_SPLITS_DIR: Path = REAL_DATA_DIR / "splits"
    REAL_MODELS_DIR: Path = REAL_DATA_DIR / "models"
    REAL_MANIFESTS_DIR: Path = REAL_DATA_DIR / "manifests"
    REAL_EVALUATION_DIR: Path = REAL_DATA_DIR / "evaluation"

    # Active Production Model Artifacts
    @property
    def production_model_dir(self) -> Path:
        return self.ARTIFACTS_DIR / "models" / "xgboost" / self.MODEL_VERSION

    @property
    def production_model_path(self) -> Path:
        return self.production_model_dir / "model.joblib"

    @property
    def production_metadata_path(self) -> Path:
        return self.production_model_dir / "metadata.json"

    @property
    def promotion_manifest_path(self) -> Path:
        return self.REAL_MANIFESTS_DIR / "production_model_promotion_manifest.json"

    @property
    def dataset_freeze_manifest_path(self) -> Path:
        return self.REAL_MANIFESTS_DIR / "dataset_freeze_manifest.json"


settings = Settings()
