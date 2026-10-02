from dataclasses import dataclass
from typing import Dict

DATASET_VERSION = "1.0.0"
DATASET_SPLIT_VERSION = "1.0.0"



@dataclass(frozen=True)
class DatasetConfig:
    """
    Reproducible ReleaseGuard dataset configuration.
    """

    dataset_version: str = DATASET_VERSION
    split_version: str = DATASET_SPLIT_VERSION

    train_ratio: float = 0.70
    validation_ratio: float = 0.15
    test_ratio: float = 0.15

    def __post_init__(self) -> None:
        total = (
            self.train_ratio
            + self.validation_ratio
            + self.test_ratio
        )

        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                "Dataset split ratios must sum to 1.0"
            )

        if any(
            ratio < 0
            for ratio in (
                self.train_ratio,
                self.validation_ratio,
                self.test_ratio,
            )
        ):
            raise ValueError(
                "Dataset split ratios must not be negative"
            )





@dataclass(frozen=True)
class DatasetRecord:
    """
    One reproducible ReleaseGuard ML training example.

    Dataset schema version: 1.0.0
    """

    # --------------------------------------------------------------
    # Identity / provenance
    # --------------------------------------------------------------

    record_id: str

    source: str

    # --------------------------------------------------------------
    # Feature data
    # --------------------------------------------------------------

    features: Dict[str, float]

    # --------------------------------------------------------------
    # Ground-truth label
    # --------------------------------------------------------------

    risk_level: str

    # --------------------------------------------------------------
    # Outcome provenance
    # --------------------------------------------------------------

    outcomes: list[str]

    def to_dict(self) -> dict:
        """
        Convert the dataset record into a JSON-serializable
        dictionary.
        """

        return {
            "dataset_version": DATASET_VERSION,
            "record_id": self.record_id,
            "source": self.source,
            "features": self.features,
            "risk_level": self.risk_level,
            "outcomes": self.outcomes,
        }
        
