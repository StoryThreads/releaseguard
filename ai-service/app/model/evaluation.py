from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


@dataclass(frozen=True)
class ModelEvaluation:
    """
    Common evaluation result for ReleaseGuard classification models.

    This evaluation protocol is intentionally model-independent so that
    Logistic Regression and XGBoost can be evaluated using exactly the
    same metrics and label ordering.
    """

    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float

    high_recall: float
    critical_recall: float

    confusion_matrix: List[List[int]]
    labels: List[str]

    brier_score: Optional[float] = None

    def to_dict(self) -> dict:
        """
        Convert evaluation results into a JSON-serializable dictionary.
        """

        return {
            "accuracy": self.accuracy,
            "macro_precision": self.macro_precision,
            "macro_recall": self.macro_recall,
            "macro_f1": self.macro_f1,
            "weighted_f1": self.weighted_f1,
            "high_recall": self.high_recall,
            "critical_recall": self.critical_recall,
            "confusion_matrix": self.confusion_matrix,
            "labels": self.labels,
            "brier_score": self.brier_score,
        }


# Backward-compatible alias used by the existing baseline evaluation tests.
BaselineEvaluation = ModelEvaluation


def evaluate_model(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str],
    probabilities: Optional[Sequence[Sequence[float]]] = None,
) -> ModelEvaluation:
    """
    Evaluate any ReleaseGuard classification model.

    The same protocol is used for:
    - Logistic Regression
    - XGBoost
    - future candidate models

    Parameters
    ----------
    y_true:
        Ground-truth labels.

    y_pred:
        Model predictions.

    labels:
        Fixed label order.

    probabilities:
        Optional class probabilities in the same order as `labels`.

    Notes
    -----
    Probability calibration is evaluated using a multiclass Brier score
    when probability predictions are supplied.

    Lower Brier score is better, but this function only records the metric;
    it does not make model-selection decisions.
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

    label_list = list(labels)

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    macro_precision = precision_score(
        y_true,
        y_pred,
        labels=label_list,
        average="macro",
        zero_division=0,
    )

    macro_recall = recall_score(
        y_true,
        y_pred,
        labels=label_list,
        average="macro",
        zero_division=0,
    )

    macro_f1 = f1_score(
        y_true,
        y_pred,
        labels=label_list,
        average="macro",
        zero_division=0,
    )

    weighted_f1 = f1_score(
        y_true,
        y_pred,
        labels=label_list,
        average="weighted",
        zero_division=0,
    )

    per_class_recall = recall_score(
        y_true,
        y_pred,
        labels=label_list,
        average=None,
        zero_division=0,
    )

    recall_by_label: Dict[str, float] = {
        label: float(recall)
        for label, recall in zip(
            label_list,
            per_class_recall,
        )
    }

    high_recall = recall_by_label.get("HIGH", 0.0)

    critical_recall = recall_by_label.get(
        "CRITICAL",
        0.0,
    )

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=label_list,
    )

    brier_score = None

    if probabilities is not None:
        brier_score = _calculate_multiclass_brier_score(
            y_true=y_true,
            probabilities=probabilities,
            labels=label_list,
        )

    return ModelEvaluation(
        accuracy=float(accuracy),
        macro_precision=float(macro_precision),
        macro_recall=float(macro_recall),
        macro_f1=float(macro_f1),
        weighted_f1=float(weighted_f1),
        high_recall=high_recall,
        critical_recall=critical_recall,
        confusion_matrix=matrix.tolist(),
        labels=label_list,
        brier_score=brier_score,
    )


def evaluate_baseline(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str],
    probabilities: Optional[Sequence[Sequence[float]]] = None,
) -> ModelEvaluation:
    """
    Backward-compatible baseline evaluation wrapper.

    The baseline uses the exact same evaluation protocol as every other
    ReleaseGuard candidate model.
    """

    return evaluate_model(
        y_true=y_true,
        y_pred=y_pred,
        labels=labels,
        probabilities=probabilities,
    )


def _calculate_multiclass_brier_score(
    y_true: Sequence[str],
    probabilities: Sequence[Sequence[float]],
    labels: Sequence[str],
) -> float:
    """
    Calculate the multiclass Brier score.

    For K classes, the multiclass score is:

        mean(sum((p_k - y_k)^2))

    where y_k is 1 for the true class and 0 otherwise.

    This requires:
    - one probability vector per sample
    - one probability per label
    - probabilities in the same order as `labels`
    """

    if len(y_true) != len(probabilities):
        raise ValueError(
            "Ground-truth labels and probabilities must contain "
            "the same number of samples."
        )

    if not probabilities:
        raise ValueError(
            "Probability predictions must contain at least one sample."
        )

    expected_class_count = len(labels)

    total = 0.0

    for index, (true_label, probability_row) in enumerate(
        zip(y_true, probabilities)
    ):
        if true_label not in labels:
            raise ValueError(
                "Ground-truth label at index "
                f"{index} is not present in the evaluation labels."
            )

        if len(probability_row) != expected_class_count:
            raise ValueError(
                "Each probability row must contain exactly "
                f"{expected_class_count} values."
            )

        probability_sum = sum(probability_row)

        if abs(probability_sum - 1.0) > 1e-6:
            raise ValueError(
                "Each probability row must sum to 1.0."
            )

        if any(
            probability < 0.0 or probability > 1.0
            for probability in probability_row
        ):
            raise ValueError(
                "Probability values must be between 0.0 and 1.0."
            )

        true_index = labels.index(true_label)

        for class_index, probability in enumerate(
            probability_row
        ):
            expected = (
                1.0
                if class_index == true_index
                else 0.0
            )

            total += (
                probability - expected
            ) ** 2

    return float(
        total / len(y_true)
    )