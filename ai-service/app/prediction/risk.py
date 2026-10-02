from typing import Dict, List

RISK_WEIGHTS = {
    "LOW": 25.0,
    "MEDIUM": 50.0,
    "HIGH": 75.0,
    "CRITICAL": 100.0,
}


def risk_level_from_probabilities(probabilities: Dict[str, float]) -> str:
    if not probabilities:
        raise ValueError("Class probabilities must not be empty.")

    return max(
        probabilities.items(),
        key=lambda item: (item[1], RISK_WEIGHTS.get(item[0], 0.0)),
    )[0]


def numerical_risk_score(probabilities: Dict[str, float]) -> float:
    if not probabilities:
        raise ValueError("Class probabilities must not be empty.")

    score = sum(
        float(probability) * RISK_WEIGHTS.get(label, 0.0)
        for label, probability in probabilities.items()
    )

    return round(max(0.0, min(100.0, score)), 6)
