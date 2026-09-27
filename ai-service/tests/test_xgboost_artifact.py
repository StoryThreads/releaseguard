import pytest

from app.model.xgboost_artifact import (
    DATASET_VERSION,
    FEATURE_VERSION,
    MODEL_NAME,
    MODEL_VERSION,
    XGBoostArtifactManager,
)
from app.model.xgboost_candidate import XGBoostCandidate


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


def train_model():

    X, y = build_training_data()

    model = XGBoostCandidate()
    model.fit(X, y)

    return model, X


def test_fitted_model_can_be_saved(tmp_path):

    model, _ = train_model()

    manager = XGBoostArtifactManager()

    artifact_path = manager.save(
        model,
        tmp_path,
    )

    assert artifact_path.exists()
    assert artifact_path.name == "model.joblib"


def test_metadata_is_saved(tmp_path):

    model, _ = train_model()

    manager = XGBoostArtifactManager()

    manager.save(
        model,
        tmp_path,
    )

    metadata = manager.load_metadata(tmp_path)

    assert metadata["model_name"] == MODEL_NAME
    assert metadata["model_version"] == MODEL_VERSION
    assert metadata["feature_version"] == FEATURE_VERSION
    assert metadata["dataset_version"] == DATASET_VERSION
    assert metadata["model_type"] == "XGBClassifier"


def test_metadata_contains_configuration(tmp_path):

    model, _ = train_model()

    manager = XGBoostArtifactManager()

    manager.save(
        model,
        tmp_path,
    )

    metadata = manager.load_metadata(tmp_path)

    assert metadata["random_state"] == 42
    assert metadata["n_estimators"] == 100
    assert metadata["max_depth"] == 4
    assert metadata["learning_rate"] == 0.1


def test_model_can_be_loaded(tmp_path):

    model, X = train_model()

    manager = XGBoostArtifactManager()

    artifact_path = manager.save(
        model,
        tmp_path,
    )

    loaded_model = manager.load(
        artifact_path,
    )

    assert isinstance(
        loaded_model,
        XGBoostCandidate,
    )

    assert loaded_model.is_fitted is True

    assert loaded_model.predict(X) == model.predict(X)


def test_loaded_model_preserves_classes(tmp_path):

    model, _ = train_model()

    manager = XGBoostArtifactManager()

    artifact_path = manager.save(
        model,
        tmp_path,
    )

    loaded_model = manager.load(
        artifact_path,
    )

    assert loaded_model.classes == model.classes


def test_loaded_model_preserves_probabilities(tmp_path):

    model, X = train_model()

    manager = XGBoostArtifactManager()

    artifact_path = manager.save(
        model,
        tmp_path,
    )

    loaded_model = manager.load(
        artifact_path,
    )

    original = model.predict_proba(X)
    loaded = loaded_model.predict_proba(X)

    for original_row, loaded_row in zip(
        original,
        loaded,
    ):
        assert loaded_row == pytest.approx(
            original_row,
            rel=1e-12,
            abs=1e-12,
        )


def test_unfitted_model_cannot_be_saved(tmp_path):

    model = XGBoostCandidate()

    manager = XGBoostArtifactManager()

    with pytest.raises(ValueError):
        manager.save(
            model,
            tmp_path,
        )


def test_missing_artifact_is_rejected(tmp_path):

    manager = XGBoostArtifactManager()

    with pytest.raises(FileNotFoundError):
        manager.load(
            tmp_path / "model.joblib"
        )


def test_missing_metadata_is_rejected(tmp_path):

    manager = XGBoostArtifactManager()

    with pytest.raises(FileNotFoundError):
        manager.load_metadata(tmp_path)