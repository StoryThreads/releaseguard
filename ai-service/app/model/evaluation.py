from dataclasses import dataclass
from typing import List, Sequence

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


@dataclass(frozen=True)
class BaselineEvaluation:
    """
    Evaluation metrics for the ReleaseGuard baseline model.
    """

    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float
    confusion_matrix: List[List[int]]
    labels: List[str]

    def to_dict(self) -> dict:
        """
        Convert evaluation metrics into a JSON-serializable dictionary.
        """

        return {
            "accuracy": self.accuracy,
            "macro_precision": self.macro_precision,
            "macro_recall": self.macro_recall,
            "macro_f1": self.macro_f1,
            "weighted_f1": self.weighted_f1,
            "confusion_matrix": self.confusion_matrix,
            "labels": self.labels,
        }


def evaluate_baseline(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str],
) -> BaselineEvaluation:
    """
    Evaluate a trained baseline model using a fixed label order.

    The label order is explicitly supplied so that the confusion
    matrix remains deterministic.
    """

    if not y_true:
        raise ValueError(
            "Evaluation labels must contain at least one sample."
        )

    if not y_pred:
        raise ValueError(
            "Predictions must contain at least one sample."
        )

    if len(y_true) != len(y_pred):
        raise ValueError(
            "Ground-truth labels and predictions must contain "
            "the same number of samples."
        )

    if not labels:
        raise ValueError(
            "At least one evaluation label is required."
        )

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    macro_precision = precision_score(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )

    macro_recall = recall_score(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )

    macro_f1 = f1_score(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )

    weighted_f1 = f1_score(
        y_true,
        y_pred,
        labels=labels,
        average="weighted",
        zero_division=0,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=labels,
    )

    return BaselineEvaluation(
        accuracy=float(accuracy),
        macro_precision=float(macro_precision),
        macro_recall=float(macro_recall),
        macro_f1=float(macro_f1),
        weighted_f1=float(weighted_f1),
        confusion_matrix=matrix.tolist(),
        labels=list(labels),
    )