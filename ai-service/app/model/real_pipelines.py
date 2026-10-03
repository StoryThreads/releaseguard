from __future__ import annotations

from typing import Any
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

LABELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class LogisticRegressionPipeline:
    """
    Serializable pipeline wrapper combining StandardScaler and LogisticRegression.
    """

    def __init__(
        self,
        scaler: StandardScaler,
        model: LogisticRegression,
    ) -> None:
        self.scaler = scaler
        self.model = model

    @property
    def classes_(self) -> np.ndarray:
        return getattr(self.model, "classes_", np.array([], dtype=np.int64))

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(
            self.scaler.transform(X)
        )

    @property
    def is_fitted(self) -> bool:
        return True

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raw_probs = self.model.predict_proba(
            self.scaler.transform(X)
        )
        probs = np.asarray(raw_probs, dtype=np.float64)
        row_sums = probs.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return probs / row_sums


class XGBoostPipeline:
    """
    Serializable pipeline wrapper for XGBoost handling sparse/non-contiguous class mapping.
    """

    def __init__(
        self,
        model: Any,
        classes: Any,
    ) -> None:
        self.model = model
        self.classes_ = np.asarray(classes, dtype=np.int64)

    @property
    def is_fitted(self) -> bool:
        return True

    @property
    def classes(self) -> list[str]:
        return [LABELS[idx] for idx in self.classes_]

    def predict(self, X: np.ndarray) -> np.ndarray:
        encoded_preds = self.model.predict(X)
        return self.classes_[np.asarray(encoded_preds, dtype=np.int64)]

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raw_probs = self.model.predict_proba(X)
        probs = np.asarray(raw_probs, dtype=np.float64)
        row_sums = probs.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return probs / row_sums
