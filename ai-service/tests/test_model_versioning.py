from pathlib import Path

from app.model.artifact import (
    DATASET_VERSION as BASELINE_DATASET_VERSION,
    FEATURE_VERSION as BASELINE_FEATURE_VERSION,
    MODEL_NAME as BASELINE_MODEL_NAME,
    MODEL_VERSION as BASELINE_MODEL_VERSION,
)

from app.model.xgboost_artifact import (
    DATASET_VERSION as XGBOOST_DATASET_VERSION,
    FEATURE_VERSION as XGBOOST_FEATURE_VERSION,
    MODEL_NAME as XGBOOST_MODEL_NAME,
    MODEL_VERSION as XGBOOST_MODEL_VERSION,
)


def test_baseline_version_metadata_is_frozen():

    assert BASELINE_MODEL_NAME == (
        "logistic_regression_baseline"
    )

    assert BASELINE_MODEL_VERSION == "1.0.0"
    assert BASELINE_FEATURE_VERSION == "1.0.0"
    assert BASELINE_DATASET_VERSION == "1.0.0"


def test_xgboost_version_metadata_is_frozen():

    assert XGBOOST_MODEL_NAME == "xgboost_candidate"

    assert XGBOOST_MODEL_VERSION == "1.0.0"
    assert XGBOOST_FEATURE_VERSION == "1.0.0"
    assert XGBOOST_DATASET_VERSION == "1.0.0"


def test_baseline_artifact_directory_is_versioned():

    artifact_directory = (
        Path("artifacts")
        / "models"
        / "baseline"
        / BASELINE_MODEL_VERSION
    )

    assert artifact_directory.name == "1.0.0"


def test_xgboost_artifact_directory_is_versioned():

    artifact_directory = (
        Path("artifacts")
        / "models"
        / "xgboost"
        / XGBOOST_MODEL_VERSION
    )

    assert artifact_directory.name == "1.0.0"


def test_baseline_artifact_contains_required_files():

    artifact_directory = (
        Path("artifacts")
        / "models"
        / "baseline"
        / BASELINE_MODEL_VERSION
    )

    assert (
        artifact_directory / "model.joblib"
    ).exists()

    assert (
        artifact_directory / "metadata.json"
    ).exists()


def test_xgboost_artifact_contains_required_files():

    artifact_directory = (
        Path("artifacts")
        / "models"
        / "xgboost"
        / XGBOOST_MODEL_VERSION
    )

    assert (
        artifact_directory / "model.joblib"
    ).exists()

    assert (
        artifact_directory / "metadata.json"
    ).exists()