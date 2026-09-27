import pytest

from app.model.baseline import (
    BaselineModelConfig,
    LogisticRegressionBaseline,
)
from app.model.training import train_baseline


def build_training_data():
    X = [
        [0.0, 0.0, 0.0],
        [0.1, 0.0, 0.1],
        [1.0, 1.0, 1.0],
        [1.1, 1.0, 1.2],
        [2.0, 2.0, 2.0],
        [2.1, 2.2, 2.0],
        [3.0, 3.0, 3.0],
        [3.1, 3.2, 3.1],
    ]

    y = [
        "LOW",
        "LOW",
        "MEDIUM",
        "MEDIUM",
        "HIGH",
        "HIGH",
        "CRITICAL",
        "CRITICAL",
    ]

    return X, y


def test_baseline_model_can_train():
    X, y = build_training_data()

    model = LogisticRegressionBaseline()

    result = model.fit(X, y)

    assert result is model
    assert model.is_fitted is True


def test_baseline_training_returns_metadata():
    X, y = build_training_data()

    result = train_baseline(X, y)

    assert result.sample_count == 8
    assert result.feature_count == 3

    assert result.classes == [
        "CRITICAL",
        "HIGH",
        "LOW",
        "MEDIUM",
    ]


def test_baseline_can_predict():
    X, y = build_training_data()

    model = LogisticRegressionBaseline()
    model.fit(X, y)

    predictions = model.predict(X)

    assert len(predictions) == len(X)

    assert all(
        prediction in {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }
        for prediction in predictions
    )


def test_baseline_returns_probabilities():
    X, y = build_training_data()

    model = LogisticRegressionBaseline()
    model.fit(X, y)

    probabilities = model.predict_proba(X)

    assert len(probabilities) == len(X)

    for row in probabilities:
        assert len(row) == 4
        assert sum(row) == pytest.approx(1.0)


def test_unfitted_model_rejects_prediction():
    X, _ = build_training_data()

    model = LogisticRegressionBaseline()

    with pytest.raises(RuntimeError):
        model.predict(X)


def test_unfitted_model_rejects_probability_prediction():
    X, _ = build_training_data()

    model = LogisticRegressionBaseline()

    with pytest.raises(RuntimeError):
        model.predict_proba(X)


def test_empty_training_data_is_rejected():
    with pytest.raises(ValueError):
        train_baseline([], [])


def test_mismatched_training_data_is_rejected():
    X, y = build_training_data()

    with pytest.raises(ValueError):
        train_baseline(X, y[:-1])


def test_empty_feature_vector_is_rejected():
    with pytest.raises(ValueError):
        train_baseline(
            [
                [],
                [],
            ],
            [
                "LOW",
                "HIGH",
            ],
        )


def test_inconsistent_feature_dimensions_are_rejected():
    with pytest.raises(ValueError):
        train_baseline(
            [
                [1.0, 2.0],
                [3.0],
            ],
            [
                "LOW",
                "HIGH",
            ],
        )


def test_training_is_deterministic():
    X, y = build_training_data()

    config = BaselineModelConfig(
        random_state=42,
        max_iter=1000,
    )

    first = train_baseline(X, y, config)
    second = train_baseline(X, y, config)

    first_predictions = first.model.predict(X)
    second_predictions = second.model.predict(X)

    first_probabilities = first.model.predict_proba(X)
    second_probabilities = second.model.predict_proba(X)

    assert first_predictions == second_predictions

    for first_row, second_row in zip(
        first_probabilities,
        second_probabilities,
    ):
        assert first_row == pytest.approx(second_row)