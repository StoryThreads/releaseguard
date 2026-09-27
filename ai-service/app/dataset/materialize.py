from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from app.dataset.schema import DatasetRecord


@dataclass(frozen=True)
class MaterializedDataset:
    """
    ML-ready representation of a prepared ReleaseGuard dataset.

    X contains feature rows in a deterministic feature order.
    y contains the corresponding risk labels.
    """

    X: List[List[float]]
    y: List[str]
    feature_names: List[str]

    @property
    def sample_count(self) -> int:
        return len(self.X)

    @property
    def feature_count(self) -> int:
        return len(self.feature_names)


def materialize_dataset(
    records: Sequence[DatasetRecord],
) -> MaterializedDataset:
    """
    Convert prepared DatasetRecord objects into an ML-ready dataset.

    Feature ordering is derived deterministically from the first record
    and must be identical for every record.

    The input records are never mutated.
    """

    if not records:
        raise ValueError(
            "Dataset must contain at least one record."
        )

    first_features = records[0].features

    if not first_features:
        raise ValueError(
            "Dataset records must contain at least one feature."
        )

    feature_names = sorted(first_features.keys())

    X: List[List[float]] = []
    y: List[str] = []

    for record in records:
        if not record.features:
            raise ValueError(
                f"Record '{record.record_id}' contains no features."
            )

        current_feature_names = sorted(
            record.features.keys()
        )

        if current_feature_names != feature_names:
            raise ValueError(
                f"Record '{record.record_id}' does not contain "
                "the same feature set as the first record."
            )

        row = [
            float(record.features[name])
            for name in feature_names
        ]

        X.append(row)
        y.append(record.risk_level)

    return MaterializedDataset(
        X=X,
        y=y,
        feature_names=feature_names,
    )