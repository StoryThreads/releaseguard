import pytest

from app.model.comparison import compare_models
from app.model.evaluation import evaluate_model


LABELS = [
    "CRITICAL",
    "HIGH",
    "LOW",
    "MEDIUM",
]


def build_evaluation():

    y_true = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]

    y_pred = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        "LOW",
        "HIGH",
        "HIGH",
        "CRITICAL",
    ]

    return evaluate_model(
        y_true,
        y_pred,
        LABELS,
    )


def test_models_use_same_evaluation_protocol():

    baseline = build_evaluation()
    xgboost = build_evaluation()

    result = compare_models(
        baseline,
        xgboost,
    )

    assert result.baseline == result.xgboost


def test_comparison_contains_required_metrics():

    baseline = build_evaluation()
    xgboost = build_evaluation()

    result = compare_models(
        baseline,
        xgboost,
    )

    expected_metrics = {
        "accuracy",
        "macro_precision",
        "macro_recall",
        "macro_f1",
        "weighted_f1",
        "high_recall",
        "critical_recall",
    }

    assert set(result.baseline.keys()) == expected_metrics
    assert set(result.xgboost.keys()) == expected_metrics


def test_label_order_must_match():

    baseline = build_evaluation()

    different_labels = [
        "HIGH",
        "CRITICAL",
        "LOW",
        "MEDIUM",
    ]

    xgboost = evaluate_model(
        y_true=[
            "LOW",
            "HIGH",
            "CRITICAL",
            "MEDIUM",
        ],
        y_pred=[
            "LOW",
            "HIGH",
            "CRITICAL",
            "MEDIUM",
        ],
        labels=different_labels,
    )

    with pytest.raises(ValueError):

        compare_models(
            baseline,
            xgboost,
        )


def test_comparison_is_serializable():

    baseline = build_evaluation()
    xgboost = build_evaluation()

    result = compare_models(
        baseline,
        xgboost,
    )

    data = result.to_dict()

    assert "baseline" in data
    assert "xgboost" in data

    assert isinstance(
        data["baseline"],
        dict,
    )

    assert isinstance(
        data["xgboost"],
        dict,
    )