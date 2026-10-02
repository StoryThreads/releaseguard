import pytest

from app.model.evaluation import (
    evaluate_baseline,
    evaluate_model,
)


LABELS = [
    "CRITICAL",
    "HIGH",
    "LOW",
    "MEDIUM",
]


def test_evaluation_returns_all_metrics():

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

    result = evaluate_model(
        y_true,
        y_pred,
        LABELS,
    )

    assert 0.0 <= result.accuracy <= 1.0
    assert 0.0 <= result.macro_precision <= 1.0
    assert 0.0 <= result.macro_recall <= 1.0
    assert 0.0 <= result.macro_f1 <= 1.0
    assert 0.0 <= result.weighted_f1 <= 1.0
    assert 0.0 <= result.high_recall <= 1.0
    assert 0.0 <= result.critical_recall <= 1.0


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

    result = evaluate_model(
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

    result = evaluate_model(
        y_true,
        y_true,
        LABELS,
    )

    assert result.accuracy == pytest.approx(1.0)
    assert result.macro_precision == pytest.approx(1.0)
    assert result.macro_recall == pytest.approx(1.0)
    assert result.macro_f1 == pytest.approx(1.0)
    assert result.weighted_f1 == pytest.approx(1.0)
    assert result.high_recall == pytest.approx(1.0)
    assert result.critical_recall == pytest.approx(1.0)


def test_high_recall_is_calculated():

    y_true = [
        "HIGH",
        "HIGH",
        "HIGH",
        "LOW",
    ]

    y_pred = [
        "HIGH",
        "HIGH",
        "LOW",
        "LOW",
    ]

    result = evaluate_model(
        y_true,
        y_pred,
        LABELS,
    )

    assert result.high_recall == pytest.approx(2 / 3)


def test_critical_recall_is_calculated():

    y_true = [
        "CRITICAL",
        "CRITICAL",
        "HIGH",
        "LOW",
    ]

    y_pred = [
        "CRITICAL",
        "HIGH",
        "HIGH",
        "LOW",
    ]

    result = evaluate_model(
        y_true,
        y_pred,
        LABELS,
    )

    assert result.critical_recall == pytest.approx(1 / 2)


def test_high_and_critical_recall_are_zero_when_absent():

    y_true = [
        "LOW",
        "MEDIUM",
        "LOW",
    ]

    y_pred = [
        "LOW",
        "MEDIUM",
        "LOW",
    ]

    result = evaluate_model(
        y_true,
        y_pred,
        LABELS,
    )

    assert result.high_recall == pytest.approx(0.0)
    assert result.critical_recall == pytest.approx(0.0)


def test_baseline_wrapper_uses_same_evaluation_protocol():

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

    baseline_result = evaluate_baseline(
        y_true,
        y_pred,
        LABELS,
    )

    model_result = evaluate_model(
        y_true,
        y_pred,
        LABELS,
    )

    assert baseline_result == model_result


def test_brier_score_is_calculated():

    y_true = [
        "LOW",
        "HIGH",
    ]

    probabilities = [
        [0.0, 0.0, 0.9, 0.1],
        [0.0, 0.8, 0.1, 0.1],
    ]

    result = evaluate_model(
        y_true=y_true,
        y_pred=[
            "LOW",
            "HIGH",
        ],
        labels=LABELS,
        probabilities=probabilities,
    )

    assert result.brier_score is not None
    assert 0.0 <= result.brier_score <= 2.0


def test_brier_score_is_zero_for_perfect_probabilities():

    y_true = [
        "LOW",
        "HIGH",
    ]

    probabilities = [
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
    ]

    result = evaluate_model(
        y_true=y_true,
        y_pred=[
            "LOW",
            "HIGH",
        ],
        labels=LABELS,
        probabilities=probabilities,
    )

    assert result.brier_score == pytest.approx(0.0)


def test_invalid_probability_length_is_rejected():

    with pytest.raises(ValueError):

        evaluate_model(
            y_true=["LOW"],
            y_pred=["LOW"],
            labels=LABELS,
            probabilities=[
                [1.0, 0.0]
            ],
        )


def test_probability_rows_must_sum_to_one():

    with pytest.raises(ValueError):

        evaluate_model(
            y_true=["LOW"],
            y_pred=["LOW"],
            labels=LABELS,
            probabilities=[
                [0.2, 0.2, 0.2, 0.2]
            ],
        )


def test_probability_values_must_be_valid():

    with pytest.raises(ValueError):

        evaluate_model(
            y_true=["LOW"],
            y_pred=["LOW"],
            labels=LABELS,
            probabilities=[
                [0.0, -0.1, 0.5, 0.6]
            ],
        )


def test_empty_ground_truth_is_rejected():

    with pytest.raises(ValueError):

        evaluate_model(
            [],
            [],
            LABELS,
        )


def test_mismatched_lengths_are_rejected():

    with pytest.raises(ValueError):

        evaluate_model(
            ["LOW"],
            ["LOW", "HIGH"],
            LABELS,
        )


def test_empty_label_set_is_rejected():

    with pytest.raises(ValueError):

        evaluate_model(
            ["LOW"],
            ["LOW"],
            [],
        )