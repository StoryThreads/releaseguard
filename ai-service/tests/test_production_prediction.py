from app.prediction.schemas import (
    ChangeSnapshotRequest,
    ChangedFileRequest,
    FindingRequest,
    PredictionRequest,
)
from app.prediction.service import PredictionService


def build_request() -> PredictionRequest:
    snapshot = ChangeSnapshotRequest(
        pullRequestNumber=999999,
        owner="releaseguard",
        repository="test-repository",
        title="Production model verification",
        sourceBranch="feature/test",
        targetBranch="main",
        headSha="abcdef1234567890",
        changedFiles=[
            ChangedFileRequest(
                filename="src/example.java",
                status="modified",
                additions=20,
                deletions=5,
                changes=25,
                patch=(
                    "@@ -1,5 +1,20 @@\n"
                    "+ example production verification change"
                ),
            )
        ],
        totalAdditions=20,
        totalDeletions=5,
        totalChanges=25,
    )

    finding = FindingRequest(
        analyzerType="CODE",
        findingType="COMPLEXITY",
        severity="MEDIUM",
        ruleId="RG-CODE-001",
        title="Production verification finding",
        message="Synthetic verification finding.",
        filePath="src/example.java",
        lineNumber=10,
    )

    return PredictionRequest(
        changeSnapshot=snapshot,
        findings=[finding],
    )


def test_production_model_loads() -> None:
    service = PredictionService.from_artifact()

    assert service.model.is_fitted is True
    assert service.metadata["model_version"] == "2.0.0"
    assert service.metadata["dataset_version"] == "2.0.0"
    assert service.metadata["feature_version"] == "1.0.0"


def test_production_prediction_returns_version_metadata() -> None:
    service = PredictionService.from_artifact()

    response = service.predict(
        build_request()
    )

    assert response.model_version == "2.0.0"
    assert response.dataset_version == "2.0.0"
    assert response.feature_version == "1.0.0"

    assert response.risk_level in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }

    assert 0.0 <= response.risk_score <= 100.0

    assert response.class_probabilities

    assert response.feature_vector

def test_production_prediction_is_reproducible() -> None:
    service = PredictionService.from_artifact()

    request = build_request()

    first = service.predict(request)
    second = service.predict(request)

    assert first.risk_level == second.risk_level
    assert first.risk_score == second.risk_score
    assert first.class_probabilities == second.class_probabilities
    assert first.feature_vector == second.feature_vector