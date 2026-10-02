import json
from dataclasses import fields
from pathlib import Path
from typing import Dict, Tuple

import joblib

from app.features.input_mapper import InputMapper
from app.features.normalizer import FeatureNormalizer
from app.features.schema import FEATURE_VERSION
from app.model.xgboost_candidate import XGBoostCandidate
from app.prediction.risk import (
    numerical_risk_score,
    risk_level_from_probabilities,
)
from app.prediction.schemas import PredictionRequest, PredictionResponse


SERVICE_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIRECTORY = SERVICE_ROOT / "artifacts" / "models" / "xgboost" / "1.0.0"
MODEL_PATH = MODEL_DIRECTORY / "model.joblib"
METADATA_PATH = MODEL_DIRECTORY / "metadata.json"


class PredictionService:
    """Build features and produce a ReleaseGuard risk prediction."""

    def __init__(
        self,
        model: XGBoostCandidate,
        metadata: Dict[str, object],
    ) -> None:
        self.model = model
        self.metadata = metadata
        self.normalizer = FeatureNormalizer()

        self._validate_metadata()

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

        if not isinstance(model, XGBoostCandidate):
            raise TypeError(
                "Configured artifact is not an XGBoostCandidate."
            )

        return cls(model, metadata)

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        internal_input = InputMapper.from_dict(
            request.model_dump(
                by_alias=True,
                exclude_none=False,
            )
        )

        from app.features.extractor import FeatureExtractor

        raw_features = FeatureExtractor().extract(internal_input)
        normalized_features = self.normalizer.normalize(raw_features)

        feature_values = [
            float(getattr(normalized_features, field.name))
            for field in fields(normalized_features)
        ]

        expected_feature_count = len(fields(normalized_features))
        if hasattr(self.model.model, "n_features_in_"):
            actual_feature_count = int(self.model.model.n_features_in_)
            if actual_feature_count != expected_feature_count:
                raise ValueError(
                    "Model feature count does not match feature schema: "
                    f"model={actual_feature_count}, "
                    f"schema={expected_feature_count}"
                )

        probabilities_list = self.model.predict_proba([feature_values])[0]
        classes = self.model.classes

        if len(classes) != len(probabilities_list):
            raise ValueError(
                "Model classes and probability output have different lengths."
            )

        probabilities = {
            label: round(float(probability), 12)
            for label, probability in zip(classes, probabilities_list)
        }

        risk_level = risk_level_from_probabilities(probabilities)
        risk_score = numerical_risk_score(probabilities)

        feature_vector = {
            field.name: float(getattr(normalized_features, field.name))
            for field in fields(normalized_features)
        }

        return PredictionResponse(
            risk_level=risk_level,
            risk_score=risk_score,
            class_probabilities=probabilities,
            feature_vector=feature_vector,
            model_name=str(self.metadata["model_name"]),
            model_version=str(self.metadata["model_version"]),
            feature_version=str(self.metadata["feature_version"]),
            dataset_version=str(self.metadata["dataset_version"]),
        )

    def _validate_metadata(self) -> None:
        required = {
            "model_name",
            "model_version",
            "feature_version",
            "dataset_version",
        }

        missing = sorted(
            key for key in required
            if key not in self.metadata
        )

        if missing:
            raise ValueError(
                "Model metadata is missing required fields: "
                + ", ".join(missing)
            )

        if str(self.metadata["feature_version"]) != FEATURE_VERSION:
            raise ValueError(
                "Model feature version does not match the active "
                f"feature schema: model={self.metadata['feature_version']} "
                f"schema={FEATURE_VERSION}"
            )
