import json
from dataclasses import fields
from pathlib import Path
from typing import Any, Dict

import joblib

from app.features.input_mapper import InputMapper
from app.features.normalizer import FeatureNormalizer
from app.features.schema import FEATURE_VERSION
from app.prediction.risk import (
    numerical_risk_score,
    risk_level_from_probabilities,
)
from app.prediction.schemas import PredictionRequest, PredictionResponse


SERVICE_ROOT = Path(__file__).resolve().parents[2]

MODEL_VERSION = "2.0.0"

MODEL_DIRECTORY = (
    SERVICE_ROOT
    / "artifacts"
    / "models"
    / "xgboost"
    / MODEL_VERSION
)

MODEL_PATH = MODEL_DIRECTORY / "model.joblib"
METADATA_PATH = MODEL_DIRECTORY / "metadata.json"


class PredictionService:
    """Build ReleaseGuard features and produce a risk prediction."""

    def __init__(
        self,
        model: Any,
        metadata: Dict[str, object],
    ) -> None:
        self.model = model
        self.metadata = metadata
        self.normalizer = FeatureNormalizer()

        self._validate_metadata()
        self._validate_model()

    @classmethod
    def from_artifact(cls) -> "PredictionService":
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model artifact not found: {MODEL_PATH}"
            )

        if not METADATA_PATH.exists():
            raise FileNotFoundError(
                f"Model metadata not found: {METADATA_PATH}"
            )

        model = joblib.load(MODEL_PATH)

        metadata = json.loads(
            METADATA_PATH.read_text(encoding="utf-8")
        )

        if not isinstance(metadata, dict):
            raise TypeError(
                "Model metadata must be a JSON object."
            )

        return cls(model, metadata)

    def predict(
        self,
        request: PredictionRequest,
    ) -> PredictionResponse:
        internal_input = InputMapper.from_dict(
            request.model_dump(
                by_alias=True,
                exclude_none=False,
            )
        )

        from app.features.extractor import FeatureExtractor

        raw_features = FeatureExtractor().extract(
            internal_input
        )

        normalized_features = self.normalizer.normalize(
            raw_features
        )

        feature_values = [
            float(
                getattr(
                    normalized_features,
                    field.name,
                )
            )
            for field in fields(normalized_features)
        ]

        expected_feature_count = len(
            fields(normalized_features)
        )

        actual_feature_count = getattr(
            self.model,
            "n_features_in_",
            None,
        )

        if actual_feature_count is not None:
            actual_feature_count = int(
                actual_feature_count
            )

            if actual_feature_count != expected_feature_count:
                raise ValueError(
                    "Model feature count does not match "
                    "feature schema: "
                    f"model={actual_feature_count}, "
                    f"schema={expected_feature_count}"
                )

        probabilities_array = self.model.predict_proba(
            [feature_values]
        )

        if len(probabilities_array) != 1:
            raise ValueError(
                "Model returned an unexpected number "
                "of probability rows."
            )

        probabilities_list = probabilities_array[0]

        classes = self._get_model_classes()

        if len(classes) != len(probabilities_list):
            raise ValueError(
                "Model classes and probability output "
                "have different lengths: "
                f"classes={len(classes)}, "
                f"probabilities={len(probabilities_list)}"
            )

        probabilities = {
            str(label): round(
                float(probability),
                12,
            )
            for label, probability in zip(
                classes,
                probabilities_list,
            )
        }

        # Ensure probabilities are numerically valid.
        probability_sum = sum(
            probabilities.values()
        )

        if probability_sum <= 0:
            raise ValueError(
                "Model returned invalid probability values."
            )

        # Normalize to protect against small floating-point
        # deviations from exactly 1.0.
        probabilities = {
            label: round(
                probability / probability_sum,
                12,
            )
            for label, probability in probabilities.items()
        }

        # Ensure all standard ReleaseGuard risk levels are present.
        for standard_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            if standard_level not in probabilities:
                probabilities[standard_level] = 0.0

        risk_level = risk_level_from_probabilities(
            probabilities
        )

        risk_score = numerical_risk_score(
            probabilities
        )

        feature_vector = {
            field.name: float(
                getattr(
                    normalized_features,
                    field.name,
                )
            )
            for field in fields(normalized_features)
        }

        return PredictionResponse(
            risk_level=risk_level,
            risk_score=risk_score,
            class_probabilities=probabilities,
            feature_vector=feature_vector,
            model_name=str(
                self.metadata["model_name"]
            ),
            model_version=str(
                self.metadata["model_version"]
            ),
            feature_version=str(
                self.metadata["feature_version"]
            ),
            dataset_version=str(
                self.metadata["dataset_version"]
            ),
        )

    def _get_model_classes(self) -> list[str]:
        """
        Return the class labels stored by the trained XGBoost
        classifier.

        The real-data model should expose classes_.
        """

        if not hasattr(self.model, "classes_"):
            raise ValueError(
                "Production model does not expose classes_. "
                "The artifact is not compatible with the "
                "ReleaseGuard prediction service."
            )

        raw_classes = self.model.classes_

        return [
            self._normalise_class_label(label)
            for label in raw_classes
        ]

    @staticmethod
    def _normalise_class_label(label: Any) -> str:
        """
        Convert numeric training labels into ReleaseGuard
        risk-level names.

        Current real-data mapping:
            0 -> LOW
            1 -> MEDIUM
            2 -> HIGH
            3 -> CRITICAL
        """

        if isinstance(label, str):
            upper = label.upper()

            if upper in {
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
            }:
                return upper

        try:
            numeric_label = int(label)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Unsupported model class label: {label!r}"
            ) from exc

        mapping = {
            0: "LOW",
            1: "MEDIUM",
            2: "HIGH",
            3: "CRITICAL",
        }

        if numeric_label not in mapping:
            raise ValueError(
                f"Unsupported model class value: "
                f"{numeric_label}"
            )

        return mapping[numeric_label]

    def _validate_model(self) -> None:
        if not hasattr(self.model, "predict_proba"):
            raise TypeError(
                "Production model does not implement "
                "predict_proba()."
            )

        if not hasattr(self.model, "classes_"):
            raise TypeError(
                "Production model does not expose "
                "classes_."
            )

        expected_classes = {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }

        actual_classes = set(
            self._get_model_classes()
        )

        if not actual_classes.issubset(
            expected_classes
        ):
            raise ValueError(
                "Production model contains unsupported "
                f"classes: {sorted(actual_classes)}"
            )

    def _validate_metadata(self) -> None:
        required = {
            "model_name",
            "model_version",
            "feature_version",
            "dataset_version",
        }

        missing = sorted(
            key
            for key in required
            if key not in self.metadata
        )

        if missing:
            raise ValueError(
                "Model metadata is missing required fields: "
                + ", ".join(missing)
            )

        metadata_model_version = str(
            self.metadata["model_version"]
        )

        if metadata_model_version != MODEL_VERSION:
            raise ValueError(
                "Production model version does not match "
                f"configured version: "
                f"metadata={metadata_model_version}, "
                f"expected={MODEL_VERSION}"
            )

        metadata_feature_version = str(
            self.metadata["feature_version"]
        )

        if metadata_feature_version != FEATURE_VERSION:
            raise ValueError(
                "Model feature version does not match "
                "the active feature schema: "
                f"model={metadata_feature_version}, "
                f"schema={FEATURE_VERSION}"
            )

        metadata_dataset_version = str(
            self.metadata["dataset_version"]
        )

        if metadata_dataset_version != "2.0.0":
            raise ValueError(
                "Production model dataset version must be "
                f"2.0.0, got {metadata_dataset_version}"
            )