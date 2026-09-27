import pytest

from app.model.xgboost_candidate import (
    XGBoostCandidate,
    XGBoostCandidateConfig,
)


def build_training_data():
    X = [
        [0.10, 0.10],
        [0.15, 0.12],
        [0.20, 0.18],
        [0.25, 0.20],
        [0.60, 0.55],
        [0.65, 0.60],
        [0.70, 0.68],
        [0.75, 0.72],
        [0.90, 0.85],
        [0.92, 0.88],
        [0.95, 0.94],
        [0.98, 0.96],
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
        "CRITICAL",
        "CRITICAL",
    ]

    return X, y


def build_model():
    return XGBoostCandidate(
        XGBoostCandidateConfig(
            random_state=42,
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
        )
    )


def test_xgboost_candidate_can_train():

    X, y = build_training_data()

    model = build_model()

    result = model.fit(X, y)

    assert result is model
    assert model.is_fitted is True


def test_xgboost_candidate_exposes_classes():

    X, y = build_training_data()

    model = build_model()
    model.fit(X, y)

    assert model.classes == [
        "CRITICAL",
        "HIGH",
        "LOW",
        "MEDIUM",
    ]


def test_xgboost_candidate_can_predict():

    X, y = build_training_data()

    model = build_model()
    model.fit(X, y)

    predictions = model.predict(X)

    assert len(predictions) == len(X)

    assert all(
        prediction in model.classes
        for prediction in predictions
    )


def test_xgboost_candidate_returns_probabilities():

    X, y = build_training_data()

    model = build_model()
    model.fit(X, y)

    probabilities = model.predict_proba(X)

    assert len(probabilities) == len(X)

    for row in probabilities:
        assert len(row) == len(model.classes)

        assert all(
            0.0 <= probability <= 1.0
            for probability in row
        )

        assert sum(row) == pytest.approx(1.0)


def test_prediction_requires_fitted_model():

    X, _ = build_training_data()

    model = build_model()

    with pytest.raises(RuntimeError):
        model.predict(X)


def test_probability_prediction_requires_fitted_model():

    X, _ = build_training_data()

    model = build_model()

    with pytest.raises(RuntimeError):
        model.predict_proba(X)


def test_classes_require_fitted_model():

    model = build_model()

    with pytest.raises(RuntimeError):
        _ = model.classes


def test_empty_training_data_is_rejected():

    model = build_model()

    with pytest.raises(ValueError):
        model.fit([], [])


def test_mismatched_training_data_is_rejected():

    model = build_model()

    with pytest.raises(ValueError):
        model.fit(
            [[0.1, 0.2]],
            ["LOW", "HIGH"],
        )


def test_single_class_training_data_is_rejected():

    model = build_model()

    with pytest.raises(ValueError):
        model.fit(
            [
                [0.1, 0.2],
                [0.2, 0.3],
            ],
            [
                "LOW",
                "LOW",
            ],
        )


def test_training_is_deterministic():

    X, y = build_training_data()

    config = XGBoostCandidateConfig(
        random_state=42,
        n_estimators=50,
        max_depth=3,
        learning_rate=0.1,
    )

    first = XGBoostCandidate(config)
    second = XGBoostCandidate(config)

    first.fit(X, y)
    second.fit(X, y)

    assert first.predict(X) == second.predict(X)

    first_probabilities = first.predict_proba(X)
    second_probabilities = second.predict_proba(X)

    for first_row, second_row in zip(
        first_probabilities,
        second_probabilities,
    ):
        assert first_row == pytest.approx(
            second_row,
            rel=1e-12,
            abs=1e-12,
        )