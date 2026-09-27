from dataclasses import dataclass
from typing import Tuple


DATA_INVENTORY_VERSION = "1.0.0"


@dataclass(frozen=True)
class HistoricalDataInventory:
    """
    Inventory of historical data currently available to ReleaseGuard
    for dataset construction.
    """

    available_change_data: bool
    available_finding_data: bool
    available_analysis_job_data: bool

    available_production_outcomes: bool
    available_deployment_outcomes: bool
    available_rollback_data: bool
    available_incident_data: bool

    change_sources: Tuple[str, ...]
    finding_sources: Tuple[str, ...]
    outcome_sources: Tuple[str, ...]

    notes: Tuple[str, ...]


RELEASEGUARD_HISTORICAL_DATA = HistoricalDataInventory(
    available_change_data=True,
    available_finding_data=True,
    available_analysis_job_data=True,

    available_production_outcomes=False,
    available_deployment_outcomes=False,
    available_rollback_data=False,
    available_incident_data=False,

    change_sources=(
        "changes",
        "ChangeSnapshot",
    ),

    finding_sources=(
        "findings",
        "FindingEntity",
    ),

    outcome_sources=(),

    notes=(
        "ReleaseGuard currently stores change and analyzer finding data.",
        "No dedicated historical production outcome source is currently available.",
        "No dedicated deployment outcome source is currently available.",
        "No dedicated rollback source is currently available.",
        "No dedicated incident source is currently available.",
        "Analyzer findings must not be treated as ground-truth outcomes.",
    ),
)