from app.dataset.data_inventory import (
    DATA_INVENTORY_VERSION,
    RELEASEGUARD_HISTORICAL_DATA,
)


def test_inventory_version():
    assert DATA_INVENTORY_VERSION == "1.0.0"


def test_change_data_is_available():
    assert RELEASEGUARD_HISTORICAL_DATA.available_change_data is True


def test_finding_data_is_available():
    assert RELEASEGUARD_HISTORICAL_DATA.available_finding_data is True


def test_analysis_job_data_is_available():
    assert (
        RELEASEGUARD_HISTORICAL_DATA.available_analysis_job_data
        is True
    )


def test_production_outcomes_are_not_currently_available():
    assert (
        RELEASEGUARD_HISTORICAL_DATA.available_production_outcomes
        is False
    )


def test_deployment_outcomes_are_not_currently_available():
    assert (
        RELEASEGUARD_HISTORICAL_DATA.available_deployment_outcomes
        is False
    )


def test_rollback_data_is_not_currently_available():
    assert (
        RELEASEGUARD_HISTORICAL_DATA.available_rollback_data
        is False
    )


def test_incident_data_is_not_currently_available():
    assert (
        RELEASEGUARD_HISTORICAL_DATA.available_incident_data
        is False
    )


def test_no_outcome_sources_are_declared():
    assert RELEASEGUARD_HISTORICAL_DATA.outcome_sources == ()


def test_analyzer_findings_are_not_ground_truth():
    assert any(
        "ground-truth" in note
        for note in RELEASEGUARD_HISTORICAL_DATA.notes
    )