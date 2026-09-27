from dataclasses import dataclass
from typing import List, Optional, Sequence

from xgboost import XGBClassifier


@dataclass(frozen=True)
class XGBoostCandidateConfig:
    """
    Configuration for the ReleaseGuard V0.5.4 XGBoost candidate.
    """

    random_state: int = 42
    n_estimators: int = 100
    max_depth: int = 4
    learning_rate: float = 0.1
    subsample: float = 1.0
    colsample_bytree: float = 1.0


class XGBoostCandidate:
    """
    ReleaseGuard V0.5.4 multiclass XGBoost candidate.

    Responsibilities:
    - Create the XGBoost classifier
    - Train it on the supplied feature matrix and labels
    - Produce class predictions
    - Produce class probabilities
    - Expose learned classes

    Dataset preparation and feature extraction remain outside
    this class.
    """

    def __init__(
        self,
        config: Optional[XGBoostCandidateConfig] = None,
    ) -> None:

        self.config = config or XGBoostCandidateConfig()

        self.model = XGBClassifier(
            objective="multi:softprob",
            n_estimators=self.config.n_estimators,
            max_depth=self.config.max_depth,
            learning_rate=self.config.learning_rate,
            subsample=self.config.subsample,
            colsample_bytree=self.config.colsample_bytree,
            random_state=self.config.random_state,
            eval_metric="mlogloss",
        )

        self._is_fitted = False
        self._classes: List[str] = []

    def fit(
        self,
        X: Sequence[Sequence[float]],
        y: Sequence[str],
    ) -> "XGBoostCandidate":
        """
        Train the XGBoost multiclass candidate.
        """

        if not X:
            raise ValueError(
                "Training data must contain at least one sample."
            )

        if not y:
            raise ValueError(
                "Training labels must contain at least one sample."
            )

        if len(X) != len(y):
            raise ValueError(
                "Feature matrix and labels must contain "
                "the same number of samples."
            )

        classes = sorted(set(y))

        if len(classes) < 2:
            raise ValueError(
                "XGBoost multiclass training requires "
                "at least two classes."
            )

        class_to_index = {
            label: index
            for index, label in enumerate(classes)
        }

        encoded_y = [
            class_to_index[label]
            for label in y
        ]

        self.model.set_params(
            num_class=len(classes)
        )

        self.model.fit(
            X,
            encoded_y,
        )

        self._classes = classes
        self._is_fitted = True

        return self

    def predict(
        self,
        X: Sequence[Sequence[float]],
    ) -> List[str]:
        """
        Predict risk levels for the supplied feature matrix.
        """

        self._require_fitted()

        predictions = self.model.predict(X)

        return [
            self._classes[int(index)]
            for index in predictions
        ]

    def predict_proba(
        self,
        X: Sequence[Sequence[float]],
    ) -> List[List[float]]:
        """
        Return class probabilities for the supplied feature matrix.
        """

        self._require_fitted()

        return self.model.predict_proba(X).tolist()

    @property
    def classes(self) -> List[str]:
        """
        Return the risk classes learned during training.
        """

        self._require_fitted()

        return list(self._classes)

    @property
    def is_fitted(self) -> bool:
        """
        Return whether the model has been trained.
        """

        return self._is_fitted

    def _require_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError(
                "XGBoost candidate must be fitted "
                "before prediction."
            )