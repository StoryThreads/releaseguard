import pytest

from app.dataset.schema import (
    DATASET_VERSION,
    DATASET_SPLIT_VERSION,
    DatasetConfig,
    DatasetRecord,
)

def test_dataset_version_is_frozen():
    assert DATASET_VERSION == "1.0.0"


def test_split_version_is_frozen():
    assert DATASET_SPLIT_VERSION == "1.0.0"


def test_default_split_configuration():
    config = DatasetConfig()

    assert config.train_ratio == 0.70
    assert config.validation_ratio == 0.15
    assert config.test_ratio == 0.15


def test_split_ratios_sum_to_one():
    config = DatasetConfig()

    total = (
        config.train_ratio
        + config.validation_ratio
        + config.test_ratio
    )

    assert total == pytest.approx(1.0)


def test_invalid_split_ratios_are_rejected():
    with pytest.raises(ValueError):
        DatasetConfig(
            train_ratio=0.80,
            validation_ratio=0.20,
            test_ratio=0.20,
        )


def test_negative_split_ratio_is_rejected():
    with pytest.raises(ValueError):
        DatasetConfig(
            train_ratio=-0.10,
            validation_ratio=0.55,
            test_ratio=0.55,
        )



def test_dataset_record_to_dict():
    record = DatasetRecord(
        record_id="test-001",
        source="releaseguard",
        features={
            "total_additions": 4.61,
            "files_changed": 2.19,
        },
        risk_level="HIGH",
        outcomes=[
            "ROLLBACK",
        ],
    )

    result = record.to_dict()

    assert result["dataset_version"] == "1.0.0"
    assert result["record_id"] == "test-001"
    assert result["source"] == "releaseguard"

    assert result["features"]["total_additions"] == 4.61
    assert result["features"]["files_changed"] == 2.19

    assert result["risk_level"] == "HIGH"
    assert result["outcomes"] == ["ROLLBACK"]


def test_dataset_record_is_deterministic():
    record = DatasetRecord(
        record_id="test-002",
        source="external",
        features={
            "files_changed": 3.0,
        },
        risk_level="MEDIUM",
        outcomes=[
            "FAILED_DEPLOYMENT",
        ],
    )

    first = record.to_dict()
    second = record.to_dict()

    assert first == second