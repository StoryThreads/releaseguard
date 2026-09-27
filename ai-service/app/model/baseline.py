from dataclasses import dataclass
from typing import List, Optional, Sequence
from sklearn.linear_model import LogisticRegression


@dataclass(frozen=True)
class BaselineModelConfig:
    """
    Configuration for the ReleaseGuard Logistic Regression baseline.
    """

    random_state: int = 42
    max_iter: int = 1000


class LogisticRegressionBaseline:
    """
    ReleaseGuard V0.5.3 Logistic Regression baseline.

    Responsibilities:
    - Create the baseline classifier
    - Train it on the supplied feature matrix and labels
    - Produce class predictions
    - Produce class probabilities
    - Expose learned classes

    Dataset preparation and feature extraction remain outside
    this class.
    """

    def __init__(
        self,
        config: Optional[BaselineModelConfig] = None,
    ) -> None:
        self.config = config or BaselineModelConfig()

        self.model = LogisticRegression(
            random_state=self.config.random_state,
            max_iter=self.config.max_iter,
        )

        self._is_fitted = False

    def fit(
        self,
        X: Sequence[Sequence[float]],
        y: Sequence[str],
    ) -> "LogisticRegressionBaseline":
        """
        Train the Logistic Regression baseline.
        """

        self.model.fit(X, y)
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

        return self.model.predict(X).tolist()

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

        return self.model.classes_.tolist()

    @property
    def is_fitted(self) -> bool:
        """
        Return whether the model has been trained.
        """

        return self._is_fitted

    def _require_fitted(self) -> None:
        if not self._is_fitted:
            raise RuntimeError(
                "Baseline model must be fitted before prediction."
            )