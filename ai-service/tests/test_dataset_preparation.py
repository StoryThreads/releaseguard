import pytest

from app.dataset.preparation import (
    DATASET_PREPARATION_VERSION,
    PreparedDatasetRecord,
    RawDatasetRecord,
    dataset_to_rows,
    prepare_dataset,
    prepare_record,
)


def test_preparation_version():
    assert DATASET_PREPARATION_VERSION == "1.0.0"


def test_prepare_record_maps_outcome_to_label():
    record = RawDatasetRecord(
        record_id="change-001",
        features={
            "total_changes": 100,
            "critical_finding_count": 1,
        },
        outcomes=("SECURITY_INCIDENT",),
    )

    prepared = prepare_record(record)

    assert isinstance(
        prepared,
        PreparedDatasetRecord,
    )

    assert prepared.record_id == "change-001"
    assert prepared.features == record.features
    assert prepared.label == "CRITICAL"


def test_multiple_outcomes_use_highest_risk():
    record = RawDatasetRecord(
        record_id="change-002",
        features={
            "total_changes": 50,
        },
        outcomes=(
            "FAILED_DEPLOYMENT",
            "ROLLBACK",
        ),
    )

    prepared = prepare_record(record)

    assert prepared.label == "HIGH"


def test_prepare_dataset_is_sorted_by_record_id():
    records = [
        RawDatasetRecord(
            record_id="change-003",
            features={"x": 3},
            outcomes=("FAILED_DEPLOYMENT",),
        ),
        RawDatasetRecord(
            record_id="change-001",
            features={"x": 1},
            outcomes=("POST_RELEASE_DEFECT",),
        ),
        RawDatasetRecord(
            record_id="change-002",
            features={"x": 2},
            outcomes=("ROLLBACK",),
        ),
    ]

    prepared = prepare_dataset(records)

    assert [
        record.record_id
        for record in prepared
    ] == [
        "change-001",
        "change-002",
        "change-003",
    ]


def test_dataset_preparation_is_deterministic():
    records = [
        RawDatasetRecord(
            record_id="b",
            features={"x": 2},
            outcomes=("ROLLBACK",),
        ),
        RawDatasetRecord(
            record_id="a",
            features={"x": 1},
            outcomes=("FAILED_DEPLOYMENT",),
        ),
    ]

    first = prepare_dataset(records)
    second = prepare_dataset(reversed(records))

    assert first == second


def test_empty_record_id_is_rejected():
    record = RawDatasetRecord(
        record_id="",
        features={"x": 1},
        outcomes=("FAILED_DEPLOYMENT",),
    )

    with pytest.raises(ValueError):
        prepare_record(record)


def test_empty_features_are_rejected():
    record = RawDatasetRecord(
        record_id="change-001",
        features={},
        outcomes=("FAILED_DEPLOYMENT",),
    )

    with pytest.raises(ValueError):
        prepare_record(record)


def test_empty_outcomes_are_rejected():
    record = RawDatasetRecord(
        record_id="change-001",
        features={"x": 1},
        outcomes=(),
    )

    with pytest.raises(ValueError):
        prepare_record(record)


def test_dataset_to_rows():
    records = [
        PreparedDatasetRecord(
            record_id="change-002",
            features={"x": 2},
            label="HIGH",
        ),
        PreparedDatasetRecord(
            record_id="change-001",
            features={"x": 1},
            label="MEDIUM",
        ),
    ]

    rows = dataset_to_rows(records)

    assert rows == [
        {
            "record_id": "change-001",
            "features": {"x": 1},
            "label": "MEDIUM",
        },
        {
            "record_id": "change-002",
            "features": {"x": 2},
            "label": "HIGH",
        },
    ]