import pytest

from app.dataset.materialize import (
    MaterializedDataset,
    materialize_dataset,
)
from app.dataset.schema import DatasetRecord


def build_records():
    return [
        DatasetRecord(
            record_id="record-001",
            source="releaseguard",
            features={
                "total_additions": 4.61,
                "files_changed": 2.19,
                "critical_finding_count": 0.0,
            },
            risk_level="LOW",
            outcomes=[],
        ),
        DatasetRecord(
            record_id="record-002",
            source="releaseguard",
            features={
                "critical_finding_count": 1.0,
                "files_changed": 3.19,
                "total_additions": 6.61,
            },
            risk_level="HIGH",
            outcomes=[
                "ROLLBACK",
            ],
        ),
    ]


def test_materialize_returns_expected_dataset():

    result = materialize_dataset(
        build_records()
    )

    assert isinstance(
        result,
        MaterializedDataset,
    )

    assert result.sample_count == 2
    assert result.feature_count == 3

    assert result.y == [
        "LOW",
        "HIGH",
    ]


def test_feature_order_is_deterministic():

    result = materialize_dataset(
        build_records()
    )

    assert result.feature_names == [
        "critical_finding_count",
        "files_changed",
        "total_additions",
    ]


def test_feature_values_follow_feature_order():

    result = materialize_dataset(
        build_records()
    )

    assert result.X == [
        [
            0.0,
            2.19,
            4.61,
        ],
        [
            1.0,
            3.19,
            6.61,
        ],
    ]


def test_feature_values_are_floats():

    result = materialize_dataset(
        build_records()
    )

    for row in result.X:
        for value in row:
            assert isinstance(
                value,
                float,
            )


def test_input_records_are_not_mutated():

    records = build_records()

    original_features = [
        dict(record.features)
        for record in records
    ]

    materialize_dataset(records)

    for record, original in zip(
        records,
        original_features,
    ):
        assert record.features == original


def test_empty_dataset_is_rejected():

    with pytest.raises(ValueError):
        materialize_dataset([])


def test_empty_features_are_rejected():

    records = [
        DatasetRecord(
            record_id="record-001",
            source="releaseguard",
            features={},
            risk_level="LOW",
            outcomes=[],
        )
    ]

    with pytest.raises(ValueError):
        materialize_dataset(records)


def test_inconsistent_feature_sets_are_rejected():

    records = [
        DatasetRecord(
            record_id="record-001",
            source="releaseguard",
            features={
                "files_changed": 2.0,
                "total_additions": 4.0,
            },
            risk_level="LOW",
            outcomes=[],
        ),
        DatasetRecord(
            record_id="record-002",
            source="releaseguard",
            features={
                "files_changed": 3.0,
                "critical_finding_count": 1.0,
            },
            risk_level="HIGH",
            outcomes=[
                "ROLLBACK",
            ],
        ),
    ]

    with pytest.raises(ValueError):
        materialize_dataset(records)


def test_materialization_is_deterministic():

    records = build_records()

    first = materialize_dataset(records)
    second = materialize_dataset(records)

    assert first == second