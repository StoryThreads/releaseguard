import json
from pathlib import Path
from typing import Any, Dict

import joblib

from app.model.xgboost_candidate import XGBoostCandidate


MODEL_NAME = "xgboost_candidate"
MODEL_VERSION = "1.0.0"
FEATURE_VERSION = "1.0.0"
DATASET_VERSION = "1.0.0"


class XGBoostArtifactManager:
    """
    Save and load the ReleaseGuard XGBoost candidate.

    Artifact format:

        model.joblib
        metadata.json
    """

    MODEL_ARTIFACT_FILENAME = "model.joblib"
    METADATA_FILENAME = "metadata.json"

    def save(
        self,
        model: XGBoostCandidate,
        artifact_directory: Path,
    ) -> Path:
        """
        Save a trained XGBoost candidate and metadata.
        """

        if not model.is_fitted:
            raise ValueError(
                "Cannot save an unfitted XGBoost candidate."
            )

        artifact_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        artifact_path = (
            artifact_directory
            / self.MODEL_ARTIFACT_FILENAME
        )

        joblib.dump(
            model,
            artifact_path,
        )

        metadata = self._build_metadata(model)

        metadata_path = (
            artifact_directory
            / self.METADATA_FILENAME
        )

        metadata_path.write_text(
            json.dumps(
                metadata,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        return artifact_path

    def load(
        self,
        artifact_path: Path,
    ) -> XGBoostCandidate:
        """
        Load a previously saved XGBoost candidate.
        """

        if not artifact_path.exists():
            raise FileNotFoundError(
                f"XGBoost artifact not found: {artifact_path}"
            )

        model: Any = joblib.load(artifact_path)

        if not isinstance(
            model,
            XGBoostCandidate,
        ):
            raise TypeError(
                "Artifact does not contain an XGBoostCandidate."
            )

        return model

    def load_metadata(
        self,
        artifact_directory: Path,
    ) -> Dict[str, Any]:
        """
        Load metadata for a saved XGBoost artifact.
        """

        metadata_path = (
            artifact_directory
            / self.METADATA_FILENAME
        )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"XGBoost metadata not found: {metadata_path}"
            )

        return json.loads(
            metadata_path.read_text(
                encoding="utf-8",
            )
        )

    @staticmethod
    def _build_metadata(
        model: XGBoostCandidate,
    ) -> Dict[str, Any]:
        """
        Build deterministic metadata describing the model artifact.
        """

        config = model.config

        return {
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "feature_version": FEATURE_VERSION,
            "dataset_version": DATASET_VERSION,
            "model_type": "XGBClassifier",
            "random_state": config.random_state,
            "n_estimators": config.n_estimators,
            "max_depth": config.max_depth,
            "learning_rate": config.learning_rate,
            "subsample": config.subsample,
            "colsample_bytree": config.colsample_bytree,
            "classes": model.classes,
        }