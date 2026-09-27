from dataclasses import dataclass
from typing import List, Optional, Sequence

from app.model.baseline import (
    BaselineModelConfig,
    LogisticRegressionBaseline,
)


@dataclass(frozen=True)
class TrainingResult:
    """
    Result of training the ReleaseGuard baseline model.
    """

    model: LogisticRegressionBaseline
    sample_count: int
    feature_count: int
    classes: List[str]


def train_baseline(
    X: Sequence[Sequence[float]],
    y: Sequence[str],
    config: Optional[BaselineModelConfig] = None
) -> TrainingResult:
    """
    Train the ReleaseGuard Logistic Regression baseline.

    Training is deterministic when the same:
    - feature matrix
    - labels
    - model configuration

    are supplied.
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

    feature_count = len(X[0])

    if feature_count == 0:
        raise ValueError(
            "Training data must contain at least one feature."
        )

    for row in X:
        if len(row) != feature_count:
            raise ValueError(
                "All feature rows must have the same "
                "number of features."
            )

    model = LogisticRegressionBaseline(config)

    model.fit(X, y)

    return TrainingResult(
        model=model,
        sample_count=len(X),
        feature_count=feature_count,
        classes=model.classes,
    )