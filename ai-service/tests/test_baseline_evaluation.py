import pytest

from app.model.evaluation import evaluate_baseline


LABELS = [
    "CRITICAL",
    "HIGH",
    "LOW",
    "MEDIUM",
]


def test_baseline_evaluation_returns_metrics():

    y_true = [
        "LOW",
        "LOW",
        "MEDIUM",
        "MEDIUM",
        "HIGH",
        "HIGH",
        "CRITICAL",
        "CRITICAL",
    ]

    y_pred = [
        "LOW",
        "LOW",
        "MEDIUM",
        "HIGH",
        "HIGH",
        "HIGH",
        "CRITICAL",
        "CRITICAL",
    ]

    result = evaluate_baseline(
        y_true,
        y_pred,
        LABELS,
    )

    assert 0.0 <= result.accuracy <= 1.0
    assert 0.0 <= result.macro_precision <= 1.0
    assert 0.0 <= result.macro_recall <= 1.0
    assert 0.0 <= result.macro_f1 <= 1.0
    assert 0.0 <= result.weighted_f1 <= 1.0


def test_confusion_matrix_uses_fixed_label_order():

    y_true = [
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
    ]

    result = evaluate_baseline(
        y_true,
        y_pred,
        LABELS,
    )

    assert result.labels == LABELS

    assert result.confusion_matrix == [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]


def test_perfect_predictions_have_perfect_metrics():

    y_true = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]

    result = evaluate_baseline(
        y_true,
        y_true,
        LABELS,
    )

    assert result.accuracy == pytest.approx(1.0)
    assert result.macro_precision == pytest.approx(1.0)
    assert result.macro_recall == pytest.approx(1.0)
    assert result.macro_f1 == pytest.approx(1.0)
    assert result.weighted_f1 == pytest.approx(1.0)


def test_empty_ground_truth_is_rejected():

    with pytest.raises(ValueError):
        evaluate_baseline(
            [],
            [],
            LABELS,
        )


def test_mismatched_lengths_are_rejected():

    with pytest.raises(ValueError):
        evaluate_baseline(
            ["LOW"],
            ["LOW", "HIGH"],
            LABELS,
        )


def test_empty_label_set_is_rejected():

    with pytest.raises(ValueError):
        evaluate_baseline(
            ["LOW"],
            ["LOW"],
            [],
        )