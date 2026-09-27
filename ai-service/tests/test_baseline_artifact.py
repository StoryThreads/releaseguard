from pathlib import Path

import pytest

from app.model.artifact import BaselineArtifactManager
from app.model.baseline import LogisticRegressionBaseline
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


def test_save_creates_artifact(tmp_path: Path):
    X, y = build_training_data()

    result = train_baseline(X, y)

    manager = BaselineArtifactManager()

    artifact_path = manager.save(
        result.model,
        tmp_path / "baseline" / "1.0.0",
    )

    assert artifact_path.exists()
    assert artifact_path.name == "model.joblib"


def test_saved_artifact_can_be_loaded(tmp_path: Path):
    X, y = build_training_data()

    result = train_baseline(X, y)

    manager = BaselineArtifactManager()

    artifact_path = manager.save(
        result.model,
        tmp_path / "baseline" / "1.0.0",
    )

    loaded_model = manager.load(artifact_path)

    assert isinstance(
        loaded_model,
        LogisticRegressionBaseline,
    )

    assert loaded_model.is_fitted is True


def test_loaded_model_produces_same_predictions(tmp_path: Path):
    X, y = build_training_data()

    result = train_baseline(X, y)

    manager = BaselineArtifactManager()

    artifact_path = manager.save(
        result.model,
        tmp_path / "baseline" / "1.0.0",
    )

    loaded_model = manager.load(artifact_path)

    original_predictions = result.model.predict(X)
    loaded_predictions = loaded_model.predict(X)

    assert original_predictions == loaded_predictions


def test_loaded_model_produces_same_probabilities(
    tmp_path: Path,
):
    X, y = build_training_data()

    result = train_baseline(X, y)

    manager = BaselineArtifactManager()

    artifact_path = manager.save(
        result.model,
        tmp_path / "baseline" / "1.0.0",
    )

    loaded_model = manager.load(artifact_path)

    original_probabilities = result.model.predict_proba(X)
    loaded_probabilities = loaded_model.predict_proba(X)

    for original_row, loaded_row in zip(
        original_probabilities,
        loaded_probabilities,
    ):
        assert original_row == pytest.approx(
            loaded_row
        )


def test_unfitted_model_cannot_be_saved(tmp_path: Path):
    manager = BaselineArtifactManager()

    model = LogisticRegressionBaseline()

    with pytest.raises(ValueError):
        manager.save(
            model,
            tmp_path / "baseline" / "1.0.0",
        )


def test_missing_artifact_is_rejected(tmp_path: Path):
    manager = BaselineArtifactManager()

    with pytest.raises(FileNotFoundError):
        manager.load(
            tmp_path / "missing" / "model.joblib"
        )

def test_metadata_file_is_created(tmp_path: Path):
    X, y = build_training_data()

    result = train_baseline(X, y)

    manager = BaselineArtifactManager()

    artifact_directory = (
        tmp_path / "baseline" / "1.0.0"
    )

    manager.save(
        result.model,
        artifact_directory,
    )

    metadata_path = (
        artifact_directory / "metadata.json"
    )

    assert metadata_path.exists()


def test_metadata_contains_model_versions(tmp_path: Path):
    X, y = build_training_data()

    result = train_baseline(X, y)

    manager = BaselineArtifactManager()

    artifact_directory = (
        tmp_path / "baseline" / "1.0.0"
    )

    manager.save(
        result.model,
        artifact_directory,
    )

    metadata = manager.load_metadata(
        artifact_directory
    )

    assert metadata["model_name"] == (
        "logistic_regression_baseline"
    )

    assert metadata["model_version"] == "1.0.0"
    assert metadata["feature_version"] == "1.0.0"
    assert metadata["dataset_version"] == "1.0.0"


def test_metadata_contains_training_configuration(
    tmp_path: Path,
):
    X, y = build_training_data()

    result = train_baseline(X, y)

    manager = BaselineArtifactManager()

    artifact_directory = (
        tmp_path / "baseline" / "1.0.0"
    )

    manager.save(
        result.model,
        artifact_directory,
    )

    metadata = manager.load_metadata(
        artifact_directory
    )

    assert metadata["model_type"] == (
        "LogisticRegression"
    )

    assert metadata["random_state"] == 42
    assert metadata["max_iter"] == 1000

    assert metadata["classes"] == [
        "CRITICAL",
        "HIGH",
        "LOW",
        "MEDIUM",
    ]


def test_missing_metadata_is_rejected(tmp_path: Path):
    manager = BaselineArtifactManager()

    with pytest.raises(FileNotFoundError):
        manager.load_metadata(
            tmp_path / "baseline" / "1.0.0"
        )