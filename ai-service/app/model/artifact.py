import json
from pathlib import Path
from typing import Any, Dict

import joblib

from app.model.baseline import LogisticRegressionBaseline


MODEL_NAME = "logistic_regression_baseline"
MODEL_VERSION = "1.0.0"
FEATURE_VERSION = "1.0.0"
DATASET_VERSION = "1.0.0"


class BaselineArtifactManager:
    """
    Save and load the ReleaseGuard Logistic Regression baseline.

    Artifact format:

        model.joblib
        metadata.json

    The model artifact contains the complete trained
    LogisticRegressionBaseline object.
    """

    MODEL_ARTIFACT_FILENAME = "model.joblib"
    METADATA_FILENAME = "metadata.json"

    def save(
        self,
        model: LogisticRegressionBaseline,
        artifact_directory: Path,
    ) -> Path:
        """
        Save a trained baseline model and its metadata.
        """

        if not model.is_fitted:
            raise ValueError(
                "Cannot save an unfitted baseline model."
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
    ) -> LogisticRegressionBaseline:
        """
        Load a previously saved baseline model.
        """

        if not artifact_path.exists():
            raise FileNotFoundError(
                f"Baseline artifact not found: {artifact_path}"
            )

        model: Any = joblib.load(artifact_path)

        if not isinstance(
            model,
            LogisticRegressionBaseline,
        ):
            raise TypeError(
                "Artifact does not contain a "
                "LogisticRegressionBaseline."
            )

        return model

    def load_metadata(
        self,
        artifact_directory: Path,
    ) -> Dict[str, Any]:
        """
        Load metadata for a saved baseline artifact.
        """

        metadata_path = (
            artifact_directory
            / self.METADATA_FILENAME
        )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Baseline metadata not found: {metadata_path}"
            )

        return json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

    @staticmethod
    def _build_metadata(
        model: LogisticRegressionBaseline,
    ) -> Dict[str, Any]:
        """
        Build deterministic metadata describing the model artifact.
        """

        return {
            "model_name": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "feature_version": FEATURE_VERSION,
            "dataset_version": DATASET_VERSION,
            "model_type": "LogisticRegression",
            "random_state": model.config.random_state,
            "max_iter": model.config.max_iter,
            "classes": model.classes,
        }