from app.dataset.data_source_policy import (
    APPROVED_EXTERNAL_SOURCE,
    RELEASEGUARD_HISTORICAL_SOURCE,
    DatasetAvailability,
    DatasetSource,
    get_dataset_source_policy,
)


def test_releaseguard_historical_data_is_not_available_for_labels():
    assert (
        RELEASEGUARD_HISTORICAL_SOURCE["source"]
        == DatasetSource.RELEASEGUARD_HISTORICAL
    )

    assert (
        RELEASEGUARD_HISTORICAL_SOURCE["availability"]
        == DatasetAvailability.NOT_AVAILABLE
    )


def test_external_dataset_requires_approval():
    assert (
        APPROVED_EXTERNAL_SOURCE["source"]
        == DatasetSource.APPROVED_EXTERNAL
    )

    assert (
        APPROVED_EXTERNAL_SOURCE["availability"]
        == DatasetAvailability.REQUIRES_APPROVAL
    )


def test_external_dataset_is_not_implicitly_approved():
    policy = get_dataset_source_policy()

    assert (
        policy["external"]["availability"]
        == DatasetAvailability.REQUIRES_APPROVAL
    )


def test_policy_contains_both_sources():
    policy = get_dataset_source_policy()

    assert "historical" in policy
    assert "external" in policy