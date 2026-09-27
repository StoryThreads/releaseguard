from dataclasses import dataclass
from typing import Any, List, Sequence, Tuple


DATASET_SPLIT_VERSION = "1.0.0"


@dataclass(frozen=True)
class DatasetSplit:
    """
    Deterministic dataset split.

    The split is performed by stable dataset order rather than
    random sampling so that the same input always produces the
    same train/validation/test assignment.
    """

    train: List[Any]
    validation: List[Any]
    test: List[Any]

    split_version: str = DATASET_SPLIT_VERSION


class DatasetSplitter:
    """
    Deterministic train/validation/test splitter.

    Default proportions:
        train      = 70%
        validation = 15%
        test       = 15%

    The input order must already represent the canonical dataset
    order established by the dataset preparation pipeline.
    """

    TRAIN_RATIO = 0.70
    VALIDATION_RATIO = 0.15
    TEST_RATIO = 0.15

    def split(self, records: Sequence[Any]) -> DatasetSplit:
        """
        Split records deterministically.

        No random seed is required because this implementation
        does not shuffle the dataset.

        Raises:
            ValueError: if the dataset is empty.
        """

        if not records:
            raise ValueError(
                "Dataset must contain at least one record"
            )

        total = len(records)

        train_end = int(total * self.TRAIN_RATIO)
        validation_end = train_end + int(
            total * self.VALIDATION_RATIO
        )

        # Guarantee that very small datasets still produce a
        # deterministic partition without invalid indexes.
        train_end = min(train_end, total)
        validation_end = min(validation_end, total)

        train = list(records[:train_end])
        validation = list(
            records[train_end:validation_end]
        )
        test = list(records[validation_end:])

        return DatasetSplit(
            train=train,
            validation=validation,
            test=test,
        )