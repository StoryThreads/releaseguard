from enum import Enum


class DatasetSource(str, Enum):
    RELEASEGUARD_HISTORICAL = "RELEASEGUARD_HISTORICAL"
    APPROVED_EXTERNAL = "APPROVED_EXTERNAL"


class DatasetAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"


RELEASEGUARD_HISTORICAL_SOURCE = {
    "source": DatasetSource.RELEASEGUARD_HISTORICAL,
    "availability": DatasetAvailability.NOT_AVAILABLE,
    "description": (
        "ReleaseGuard currently contains change and finding data, "
        "but does not contain sufficient historical post-change "
        "outcomes for supervised risk-label construction."
    ),
}


APPROVED_EXTERNAL_SOURCE = {
    "source": DatasetSource.APPROVED_EXTERNAL,
    "availability": DatasetAvailability.REQUIRES_APPROVAL,
    "description": (
        "An external dataset may be used only after its provenance, "
        "license, schema compatibility, and label quality have been "
        "reviewed and explicitly approved."
    ),
}


def get_dataset_source_policy() -> dict:
    """
    Return the current dataset-source policy.

    No external dataset is approved by default.
    """

    return {
        "historical": RELEASEGUARD_HISTORICAL_SOURCE,
        "external": APPROVED_EXTERNAL_SOURCE,
    }