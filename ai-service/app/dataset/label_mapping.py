from app.dataset.label_policy import RiskLevel


RISK_LEVEL_DEFINITIONS = {
    RiskLevel.LOW: {
        "description": (
            "No qualifying adverse post-change outcome was observed."
        ),
        "qualifying_outcomes": [],
    },
    RiskLevel.MEDIUM: {
        "description": (
            "A limited adverse outcome occurred without evidence "
            "of a major production impact."
        ),
        "qualifying_outcomes": [
            "FAILED_DEPLOYMENT",
            "POST_RELEASE_DEFECT",
        ],
    },
    RiskLevel.HIGH: {
        "description": (
            "A significant operational or production impact occurred."
        ),
        "qualifying_outcomes": [
            "ROLLBACK",
            "PRODUCTION_INCIDENT",
            "RELIABILITY_INCIDENT",
        ],
    },
    RiskLevel.CRITICAL: {
        "description": (
            "A severe security-related incident occurred."
        ),
        "qualifying_outcomes": [
            "SECURITY_INCIDENT",
        ],
    },
}


def get_risk_level_definition(risk_level: RiskLevel) -> dict:
    """
    Return the formal definition for a ReleaseGuard risk level.
    """

    if not isinstance(risk_level, RiskLevel):
        raise ValueError(
            f"Unknown risk level: {risk_level}"
        )

    return RISK_LEVEL_DEFINITIONS[risk_level]