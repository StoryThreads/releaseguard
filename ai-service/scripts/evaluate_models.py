import json
from pathlib import Path
from typing import Dict, List, Sequence

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from app.model.baseline import (
    BaselineModelConfig,
    LogisticRegressionBaseline,
)
from app.model.xgboost_candidate import XGBoostCandidate
from app.model.xgboost_training import train_xgboost_candidate


LABELS = [
    "CRITICAL",
    "HIGH",
    "LOW",
    "MEDIUM",
]

DATASET_VERSION = "1.0.0"
FEATURE_VERSION = "1.0.0"
MODEL_VERSION = "1.0.0"

ROOT_DIR = Path(__file__).resolve().parents[1]

ARTIFACT_DIR = (
    ROOT_DIR
    / "artifacts"
    / "evaluation"
    / "1.0.0"
)

OUTPUT_FILE = ARTIFACT_DIR / "evaluation.json"


def build_evaluation_data():
    """
    Deterministic development/evaluation dataset.

    IMPORTANT:
    This is synthetic data and must not be interpreted
    as production model performance.
    """

    X = [
        [1.0, 1.0, 0.1, 0.1],
        [1.2, 1.0, 0.1, 0.2],
        [1.0, 1.3, 0.2, 0.1],
        [1.1, 1.2, 0.1, 0.2],

        [3.0, 2.5, 0.4, 0.5],
        [3.2, 2.7, 0.5, 0.4],
        [2.8, 2.6, 0.4, 0.6],
        [3.1, 2.4, 0.5, 0.5],

        [5.0, 4.5, 0.7, 0.8],
        [5.2, 4.7, 0.8, 0.7],
        [4.8, 4.6, 0.7, 0.9],
        [5.1, 4.4, 0.8, 0.8],

        [7.0, 6.5, 0.9, 1.0],
        [7.2, 6.7, 1.0, 0.9],
        [6.8, 6.6, 0.9, 1.1],
        [7.1, 6.4, 1.0, 1.0],
    ]

    y = [
        "LOW",
        "LOW",
        "LOW",
        "LOW",

        "MEDIUM",
        "MEDIUM",
        "MEDIUM",
        "MEDIUM",

        "HIGH",
        "HIGH",
        "HIGH",
        "HIGH",

        "CRITICAL",
        "CRITICAL",
        "CRITICAL",
        "CRITICAL",
    ]

    return X, y


def calculate_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
) -> Dict:
    """
    Calculate the complete V0.5.5 evaluation protocol.
    """

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=LABELS,
    )

    high_index = LABELS.index("HIGH")
    critical_index = LABELS.index("CRITICAL")

    high_tp = matrix[high_index][high_index]
    high_total = sum(matrix[high_index])

    critical_tp = matrix[critical_index][critical_index]
    critical_total = sum(matrix[critical_index])

    high_recall = (
        high_tp / high_total
        if high_total > 0
        else 0.0
    )

    critical_recall = (
        critical_tp / critical_total
        if critical_total > 0
        else 0.0
    )

    return {
        "accuracy": float(
            accuracy_score(y_true, y_pred)
        ),
        "macro_precision": float(
            precision_score(
                y_true,
                y_pred,
                labels=LABELS,
                average="macro",
                zero_division=0,
            )
        ),
        "macro_recall": float(
            recall_score(
                y_true,
                y_pred,
                labels=LABELS,
                average="macro",
                zero_division=0,
            )
        ),
        "macro_f1": float(
            f1_score(
                y_true,
                y_pred,
                labels=LABELS,
                average="macro",
                zero_division=0,
            )
        ),
        "weighted_f1": float(
            f1_score(
                y_true,
                y_pred,
                labels=LABELS,
                average="weighted",
                zero_division=0,
            )
        ),
        "high_recall": float(high_recall),
        "critical_recall": float(critical_recall),
        "confusion_matrix": matrix.tolist(),
        "labels": LABELS,
    }


def evaluate_baseline(
    X: Sequence[Sequence[float]],
    y: Sequence[str],
) -> Dict:
    """
    Train and evaluate Logistic Regression.
    """

    model = LogisticRegressionBaseline(
        BaselineModelConfig(
            random_state=42,
            max_iter=1000,
        )
    )

    model.fit(X, y)

    predictions = model.predict(X)

    return {
        "model_name": "logistic_regression_baseline",
        "model_type": "LogisticRegression",
        "model_version": MODEL_VERSION,
        "metrics": calculate_metrics(y, predictions),
    }


def evaluate_xgboost(
    X: Sequence[Sequence[float]],
    y: Sequence[str],
) -> Dict:
    """
    Train and evaluate XGBoost using the same
    evaluation protocol as the baseline.
    """

    result = train_xgboost_candidate(
        X,
        y,
    )

    model = result.model

    predictions = model.predict(X)

    return {
        "model_name": "xgboost_candidate",
        "model_type": "XGBoost",
        "model_version": MODEL_VERSION,
        "metrics": calculate_metrics(y, predictions),
    }


def build_comparison(
    baseline: Dict,
    xgboost: Dict,
) -> Dict:
    """
    Compare models descriptively.

    No winner/ranking is produced.
    """

    baseline_metrics = baseline["metrics"]
    xgboost_metrics = xgboost["metrics"]

    metric_names = [
        "accuracy",
        "macro_precision",
        "macro_recall",
        "macro_f1",
        "weighted_f1",
        "high_recall",
        "critical_recall",
    ]

    comparison = {}

    for metric in metric_names:
        comparison[metric] = {
            "baseline": baseline_metrics[metric],
            "xgboost": xgboost_metrics[metric],
            "difference": (
                xgboost_metrics[metric]
                - baseline_metrics[metric]
            ),
        }

    return comparison


def print_metrics(
    result: Dict,
) -> None:

    metrics = result["metrics"]

    print()
    print("=" * 60)
    print(result["model_name"])
    print("=" * 60)

    print(
        f"Model Type       : {result['model_type']}"
    )

    print(
        f"Model Version    : {result['model_version']}"
    )

    print(
        f"Accuracy         : {metrics['accuracy']:.6f}"
    )

    print(
        f"Macro Precision  : {metrics['macro_precision']:.6f}"
    )

    print(
        f"Macro Recall     : {metrics['macro_recall']:.6f}"
    )

    print(
        f"Macro F1         : {metrics['macro_f1']:.6f}"
    )

    print(
        f"Weighted F1      : {metrics['weighted_f1']:.6f}"
    )

    print(
        f"HIGH Recall      : {metrics['high_recall']:.6f}"
    )

    print(
        f"CRITICAL Recall  : {metrics['critical_recall']:.6f}"
    )

    print()
    print("Confusion Matrix")
    print("-" * 30)

    for row in metrics["confusion_matrix"]:
        print(row)


def main() -> None:

    print("=" * 60)
    print("ReleaseGuard V0.5.5 Model Evaluation")
    print("=" * 60)

    print()
    print("WARNING:")
    print(
        "Evaluation uses synthetic development data."
    )
    print(
        "These metrics are NOT production performance."
    )

    print()
    print(
        f"Dataset Version : {DATASET_VERSION}"
    )

    print(
        f"Feature Version : {FEATURE_VERSION}"
    )

    X, y = build_evaluation_data()

    baseline = evaluate_baseline(
        X,
        y,
    )

    xgboost = evaluate_xgboost(
        X,
        y,
    )

    print_metrics(baseline)
    print_metrics(xgboost)

    comparison = build_comparison(
        baseline,
        xgboost,
    )

    print()
    print("=" * 60)
    print("BASELINE / XGBOOST COMPARISON")
    print("=" * 60)

    for metric, values in comparison.items():

        print(
            f"{metric:18} "
            f"Baseline={values['baseline']:.6f} "
            f"XGBoost={values['xgboost']:.6f} "
            f"Difference={values['difference']:+.6f}"
        )

    evaluation = {
        "evaluation_version": "1.0.0",
        "dataset_version": DATASET_VERSION,
        "feature_version": FEATURE_VERSION,
        "data_type": "synthetic_development_data",
        "production_ready": False,
        "baseline": baseline,
        "xgboost": xgboost,
        "comparison": comparison,
    }

    ARTIFACT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            evaluation,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("Evaluation saved")
    print("=" * 60)

    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()