import json

import pytest

from app.model.artifact import (
    BaselineArtifactManager,
    DATASET_VERSION,
    FEATURE_VERSION,
    MODEL_NAME,
    MODEL_VERSION,
)
from app.model.baseline import (
    BaselineModelConfig,
    LogisticRegressionBaseline,
)


def build_training_data():
    X = [
        [1.0, 0.0, 0.0],
        [1.2, 0.1, 0.0],
        [0.0, 1.0, 0.0],
        [0.1, 1.2, 0.0],
        [0.0, 0.0, 1.0],
        [0.1, 0.0, 1.2],
        [0.8, 0.2, 0.1],
        [0.2, 0.8, 0.1],
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


def train_model():
    X, y = build_training_data()

    model = LogisticRegressionBaseline(
        BaselineModelConfig(
            random_state=42,
            max_iter=1000,
        )
    )

    model.fit(X, y)

    return model, X, y


def test_fitted_model_can_be_saved(tmp_path):
    model, _, _ = train_model()

    manager = BaselineArtifactManager()

    artifact_path = manager.save(
        model,
        tmp_path,
    )

    assert artifact_path.exists()
    assert artifact_path.name == "model.joblib"


def test_model_and_metadata_files_are_created(tmp_path):
    model, _, _ = train_model()

    manager = BaselineArtifactManager()

    manager.save(model, tmp_path)

    assert (tmp_path / "model.joblib").exists()
    assert (tmp_path / "metadata.json").exists()


def test_saved_metadata_contains_expected_versions(tmp_path):
    model, _, _ = train_model()

    manager = BaselineArtifactManager()

    manager.save(model, tmp_path)

    metadata = manager.load_metadata(tmp_path)

    assert metadata["model_name"] == MODEL_NAME
    assert metadata["model_version"] == MODEL_VERSION
    assert metadata["feature_version"] == FEATURE_VERSION
    assert metadata["dataset_version"] == DATASET_VERSION


def test_saved_metadata_contains_model_configuration(tmp_path):
    model, _, _ = train_model()

    manager = BaselineArtifactManager()

    manager.save(model, tmp_path)

    metadata = manager.load_metadata(tmp_path)

    assert metadata["model_type"] == "LogisticRegression"
    assert metadata["random_state"] == 42
    assert metadata["max_iter"] == 1000


def test_saved_metadata_contains_classes(tmp_path):
    model, _, _ = train_model()

    manager = BaselineArtifactManager()

    manager.save(model, tmp_path)

    metadata = manager.load_metadata(tmp_path)

    assert metadata["classes"] == model.classes


def test_saved_model_can_be_loaded(tmp_path):
    model, _, _ = train_model()

    manager = BaselineArtifactManager()

    artifact_path = manager.save(
        model,
        tmp_path,
    )

    loaded_model = manager.load(artifact_path)

    assert loaded_model.is_fitted
    assert loaded_model.classes == model.classes


def test_loaded_model_produces_same_predictions(tmp_path):
    model, X, _ = train_model()

    manager = BaselineArtifactManager()

    artifact_path = manager.save(
        model,
        tmp_path,
    )

    loaded_model = manager.load(artifact_path)

    assert loaded_model.predict(X) == model.predict(X)


def test_loaded_model_produces_same_probabilities(tmp_path):
    model, X, _ = train_model()

    manager = BaselineArtifactManager()

    artifact_path = manager.save(
        model,
        tmp_path,
    )

    loaded_model = manager.load(artifact_path)

    original_probabilities = model.predict_proba(X)
    loaded_probabilities = loaded_model.predict_proba(X)

    for loaded_row, original_row in zip(
        loaded_probabilities,
        original_probabilities,
    ):
        assert loaded_row == pytest.approx(
            original_row,
            rel=1e-12,
            abs=1e-12,
        )


def test_unfitted_model_cannot_be_saved(tmp_path):
    model = LogisticRegressionBaseline()

    manager = BaselineArtifactManager()

    with pytest.raises(ValueError):
        manager.save(model, tmp_path)


def test_missing_artifact_is_rejected(tmp_path):
    manager = BaselineArtifactManager()

    missing_path = tmp_path / "model.joblib"

    with pytest.raises(FileNotFoundError):
        manager.load(missing_path)


def test_missing_metadata_is_rejected(tmp_path):
    manager = BaselineArtifactManager()

    with pytest.raises(FileNotFoundError):
        manager.load_metadata(tmp_path)


def test_invalid_artifact_type_is_rejected(tmp_path):
    manager = BaselineArtifactManager()

    invalid_path = tmp_path / "invalid.joblib"

    import joblib

    joblib.dump(
        {"not": "a baseline model"},
        invalid_path,
    )

    with pytest.raises(TypeError):
        manager.load(invalid_path)