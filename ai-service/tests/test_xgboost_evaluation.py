from app.model.evaluation import evaluate_baseline
from app.model.xgboost_candidate import XGBoostCandidate


LABELS = [
    "CRITICAL",
    "HIGH",
    "LOW",
    "MEDIUM",
]


def test_xgboost_uses_baseline_evaluation_protocol():

    X = [
        [0.10, 0.10],
        [0.15, 0.12],
        [0.20, 0.18],
        [0.60, 0.55],
        [0.65, 0.60],
        [0.70, 0.68],
        [0.90, 0.85],
        [0.92, 0.88],
        [0.95, 0.94],
        [0.98, 0.96],
        [0.99, 0.97],
        [0.995, 0.98],
    ]

    y_true = [
        "LOW",
        "LOW",
        "LOW",
        "MEDIUM",
        "MEDIUM",
        "MEDIUM",
        "HIGH",
        "HIGH",
        "HIGH",
        "CRITICAL",
        "CRITICAL",
        "CRITICAL",
    ]

    model = XGBoostCandidate()
    model.fit(X, y_true)

    y_pred = model.predict(X)

    result = evaluate_baseline(
        y_true,
        y_pred,
        LABELS,
    )

    assert result.labels == LABELS
    assert len(result.confusion_matrix) == 4
    assert all(
        len(row) == 4
        for row in result.confusion_matrix
    )

    assert 0.0 <= result.accuracy <= 1.0
    assert 0.0 <= result.macro_precision <= 1.0
    assert 0.0 <= result.macro_recall <= 1.0
    assert 0.0 <= result.macro_f1 <= 1.0
    assert 0.0 <= result.weighted_f1 <= 1.0