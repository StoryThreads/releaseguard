from dataclasses import dataclass
from typing import Dict

from app.model.evaluation import ModelEvaluation


@dataclass(frozen=True)
class ModelComparison:
    """
    Structured comparison between candidate models.

    This class reports metric values without declaring a winner.
    """

    baseline: Dict[str, float]
    xgboost: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "baseline": dict(self.baseline),
            "xgboost": dict(self.xgboost),
        }


def compare_models(
    baseline: ModelEvaluation,
    xgboost: ModelEvaluation,
) -> ModelComparison:
    """
    Compare Logistic Regression and XGBoost using the same metrics.

    This function intentionally does not rank or select a model.
    """

    if baseline.labels != xgboost.labels:
        raise ValueError(
            "Baseline and XGBoost evaluations must use "
            "the same label order."
        )

    return ModelComparison(
        baseline=_metric_dict(baseline),
        xgboost=_metric_dict(xgboost),
    )


def _metric_dict(
    result: ModelEvaluation,
) -> Dict[str, float]:
    return {
        "accuracy": result.accuracy,
        "macro_precision": result.macro_precision,
        "macro_recall": result.macro_recall,
        "macro_f1": result.macro_f1,
        "weighted_f1": result.weighted_f1,
        "high_recall": result.high_recall,
        "critical_recall": result.critical_recall,
    }