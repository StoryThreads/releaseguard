import pytest

from app.model.xgboost_candidate import (
    XGBoostCandidateConfig,
)
from app.model.xgboost_training import (
    train_xgboost_candidate,
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


def test_training_returns_result():

    X, y = build_training_data()

    result = train_xgboost_candidate(X, y)

    assert result.model.is_fitted is True
    assert result.sample_count == 12
    assert result.feature_count == 2
    assert result.classes == [
        "CRITICAL",
        "HIGH",
        "LOW",
        "MEDIUM",
    ]


def test_training_accepts_custom_configuration():

    X, y = build_training_data()

    config = XGBoostCandidateConfig(
        random_state=42,
        n_estimators=25,
        max_depth=3,
    )

    result = train_xgboost_candidate(
        X,
        y,
        config,
    )

    assert result.model.is_fitted is True
    assert result.model.config == config


def test_empty_features_are_rejected():

    with pytest.raises(ValueError):
        train_xgboost_candidate([], [])


def test_empty_labels_are_rejected():

    with pytest.raises(ValueError):
        train_xgboost_candidate(
            [[0.1, 0.2]],
            [],
        )


def test_mismatched_lengths_are_rejected():

    with pytest.raises(ValueError):
        train_xgboost_candidate(
            [[0.1, 0.2]],
            ["LOW", "HIGH"],
        )


def test_empty_feature_row_is_rejected():

    with pytest.raises(ValueError):
        train_xgboost_candidate(
            [[]],
            ["LOW"],
        )


def test_inconsistent_feature_width_is_rejected():

    with pytest.raises(ValueError):
        train_xgboost_candidate(
            [
                [0.1, 0.2],
                [0.3],
            ],
            [
                "LOW",
                "HIGH",
            ],
        )