import pytest
from app.dataset.label_policy import (
    FAILED_DEPLOYMENT,
    POST_RELEASE_DEFECT,
    ROLLBACK,
    PRODUCTION_INCIDENT,
    RELIABILITY_INCIDENT,
    SECURITY_INCIDENT,
    RiskLevel,
    map_outcome_to_risk,
    map_outcomes_to_risk,
)


def test_failed_deployment_maps_to_medium():
    assert (
        map_outcome_to_risk(FAILED_DEPLOYMENT)
        == RiskLevel.MEDIUM
    )


def test_post_release_defect_maps_to_medium():
    assert (
        map_outcome_to_risk(POST_RELEASE_DEFECT)
        == RiskLevel.MEDIUM
    )


def test_rollback_maps_to_high():
    assert (
        map_outcome_to_risk(ROLLBACK)
        == RiskLevel.HIGH
    )


def test_production_incident_maps_to_high():
    assert (
        map_outcome_to_risk(PRODUCTION_INCIDENT)
        == RiskLevel.HIGH
    )


def test_reliability_incident_maps_to_high():
    assert (
        map_outcome_to_risk(RELIABILITY_INCIDENT)
        == RiskLevel.HIGH
    )


def test_security_incident_maps_to_critical():
    assert (
        map_outcome_to_risk(SECURITY_INCIDENT)
        == RiskLevel.CRITICAL
    )


def test_unknown_outcome_is_rejected():
    with pytest.raises(ValueError):
        map_outcome_to_risk("UNKNOWN_OUTCOME")
        
def test_multiple_outcomes_use_highest_risk():
    assert (
        map_outcomes_to_risk([
            FAILED_DEPLOYMENT,
            ROLLBACK,
        ])
        == RiskLevel.HIGH
    )


def test_security_incident_overrides_lower_risk_outcomes():
    assert (
        map_outcomes_to_risk([
            FAILED_DEPLOYMENT,
            ROLLBACK,
            SECURITY_INCIDENT,
        ])
        == RiskLevel.CRITICAL
    )


def test_multiple_medium_outcomes_remain_medium():
    assert (
        map_outcomes_to_risk([
            FAILED_DEPLOYMENT,
            POST_RELEASE_DEFECT,
        ])
        == RiskLevel.MEDIUM
    )


def test_empty_outcomes_are_rejected():
    with pytest.raises(ValueError):
        map_outcomes_to_risk([])