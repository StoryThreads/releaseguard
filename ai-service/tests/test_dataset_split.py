import pytest

from app.dataset.split import (
    DATASET_SPLIT_VERSION,
    DatasetSplitter,
)


def test_default_split_is_70_15_15():

    records = list(range(20))

    splitter = DatasetSplitter()

    result = splitter.split(records)

    assert len(result.train) == 14
    assert len(result.validation) == 3
    assert len(result.test) == 3


def test_split_preserves_record_order():

    records = list(range(20))

    result = DatasetSplitter().split(records)

    assert result.train == list(range(14))
    assert result.validation == [14, 15, 16]
    assert result.test == [17, 18, 19]


def test_split_is_deterministic():

    records = list(range(20))

    splitter = DatasetSplitter()

    first = splitter.split(records)
    second = splitter.split(records)

    assert first == second


def test_all_records_are_preserved():

    records = list(range(20))

    result = DatasetSplitter().split(records)

    combined = (
        result.train
        + result.validation
        + result.test
    )

    assert combined == records


def test_no_record_is_duplicated():

    records = list(range(20))

    result = DatasetSplitter().split(records)

    combined = (
        result.train
        + result.validation
        + result.test
    )

    assert len(combined) == len(set(combined))


def test_empty_dataset_is_rejected():

    with pytest.raises(ValueError):

        DatasetSplitter().split([])


def test_split_version_is_frozen():

    result = DatasetSplitter().split(
        list(range(20))
    )

    assert result.split_version == "1.0.0"
    assert DATASET_SPLIT_VERSION == "1.0.0"