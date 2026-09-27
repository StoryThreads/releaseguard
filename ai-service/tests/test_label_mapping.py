import pytest

from app.dataset.label_mapping import (
    RISK_LEVEL_DEFINITIONS,
    get_risk_level_definition,
)
from app.dataset.label_policy import RiskLevel


def test_all_risk_levels_have_definitions():
    assert set(RISK_LEVEL_DEFINITIONS.keys()) == {
        RiskLevel.LOW,
        RiskLevel.MEDIUM,
        RiskLevel.HIGH,
        RiskLevel.CRITICAL,
    }


def test_low_definition():
    definition = get_risk_level_definition(RiskLevel.LOW)

    assert definition["description"]
    assert definition["qualifying_outcomes"] == []


def test_medium_definition():
    definition = get_risk_level_definition(RiskLevel.MEDIUM)

    assert definition["description"]
    assert set(definition["qualifying_outcomes"]) == {
        "FAILED_DEPLOYMENT",
        "POST_RELEASE_DEFECT",
    }


def test_high_definition():
    definition = get_risk_level_definition(RiskLevel.HIGH)

    assert definition["description"]
    assert set(definition["qualifying_outcomes"]) == {
        "ROLLBACK",
        "PRODUCTION_INCIDENT",
        "RELIABILITY_INCIDENT",
    }


def test_critical_definition():
    definition = get_risk_level_definition(RiskLevel.CRITICAL)

    assert definition["description"]
    assert definition["qualifying_outcomes"] == [
        "SECURITY_INCIDENT",
    ]


def test_unknown_risk_level_is_rejected():
    with pytest.raises(ValueError):
        get_risk_level_definition("UNKNOWN")


def test_definitions_are_deterministic():
    first = get_risk_level_definition(RiskLevel.HIGH)
    second = get_risk_level_definition(RiskLevel.HIGH)

    assert first == second