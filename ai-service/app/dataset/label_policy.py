from enum import Enum


DATASET_VERSION = "1.0.0"


class RiskLevel(str, Enum):
    """
    ReleaseGuard V0.5 risk levels.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# ------------------------------------------------------------------
# Outcome categories
# ------------------------------------------------------------------

PRODUCTION_INCIDENT = "PRODUCTION_INCIDENT"
ROLLBACK = "ROLLBACK"
FAILED_DEPLOYMENT = "FAILED_DEPLOYMENT"
POST_RELEASE_DEFECT = "POST_RELEASE_DEFECT"
SECURITY_INCIDENT = "SECURITY_INCIDENT"
RELIABILITY_INCIDENT = "RELIABILITY_INCIDENT"


# ------------------------------------------------------------------
# V0.5 initial outcome -> risk mapping
# ------------------------------------------------------------------

OUTCOME_RISK_MAPPING = {
    FAILED_DEPLOYMENT: RiskLevel.MEDIUM,
    POST_RELEASE_DEFECT: RiskLevel.MEDIUM,
    ROLLBACK: RiskLevel.HIGH,
    PRODUCTION_INCIDENT: RiskLevel.HIGH,
    RELIABILITY_INCIDENT: RiskLevel.HIGH,
    SECURITY_INCIDENT: RiskLevel.CRITICAL,
}


def map_outcome_to_risk(outcome: str) -> RiskLevel:
    """
    Convert an observed change outcome into the corresponding
    ReleaseGuard V0.5 risk level.

    Raises:
        ValueError: if the outcome is unknown.
    """

    try:
        return OUTCOME_RISK_MAPPING[outcome]
    except KeyError as exc:
        raise ValueError(
            f"Unknown outcome: {outcome}"
        ) from exc
        
# ------------------------------------------------------------------
# Outcome precedence
# ------------------------------------------------------------------

RISK_PRECEDENCE = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


def map_outcomes_to_risk(outcomes: list[str]) -> RiskLevel:
    """
    Convert one or more observed outcomes into a single
    ReleaseGuard V0.5 ground-truth risk level.

    When multiple outcomes are associated with the same change,
    the highest-severity mapped outcome is used.
    """

    if not outcomes:
        raise ValueError(
            "At least one outcome is required"
        )

    mapped_levels = [
        map_outcome_to_risk(outcome)
        for outcome in outcomes
    ]

    return max(
        mapped_levels,
        key=lambda level: RISK_PRECEDENCE[level],
    )