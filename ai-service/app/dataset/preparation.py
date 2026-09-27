from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

from app.dataset.label_policy import (
    RiskLevel,
    map_outcomes_to_risk,
)


DATASET_PREPARATION_VERSION = "1.0.0"


@dataclass(frozen=True)
class RawDatasetRecord:
    """
    Raw supervised-learning record.

    features:
        Already extracted ReleaseGuard features.

    outcomes:
        Observed post-change outcomes used to derive the
        ground-truth risk label.
    """

    record_id: str
    features: Dict[str, Any]
    outcomes: Tuple[str, ...]


@dataclass(frozen=True)
class PreparedDatasetRecord:
    """
    Deterministically prepared training record.
    """

    record_id: str
    features: Dict[str, Any]
    label: str


def prepare_record(
    record: RawDatasetRecord,
) -> PreparedDatasetRecord:
    """
    Convert one raw labeled record into a training record.
    """

    if not record.record_id:
        raise ValueError("record_id must not be empty")

    if not record.features:
        raise ValueError("features must not be empty")

    if not record.outcomes:
        raise ValueError(
            "At least one observed outcome is required"
        )

    risk_level = map_outcomes_to_risk(
        list(record.outcomes)
    )

    return PreparedDatasetRecord(
        record_id=record.record_id,
        features=dict(record.features),
        label=risk_level.value,
    )


def prepare_dataset(
    records: Iterable[RawDatasetRecord],
) -> List[PreparedDatasetRecord]:
    """
    Prepare an entire dataset deterministically.

    Records are sorted by record_id so that dataset preparation
    does not depend on input iteration order.
    """

    records_list = list(records)

    prepared = [
        prepare_record(record)
        for record in records_list
    ]

    prepared.sort(
        key=lambda record: record.record_id
    )

    return prepared


def dataset_to_rows(
    records: Iterable[PreparedDatasetRecord],
) -> List[Dict[str, Any]]:
    """
    Convert prepared records into deterministic row dictionaries.
    """

    rows = [
        {
            "record_id": record.record_id,
            "features": dict(record.features),
            "label": record.label,
        }
        for record in records
    ]

    rows.sort(
        key=lambda row: row["record_id"]
    )

    return rows