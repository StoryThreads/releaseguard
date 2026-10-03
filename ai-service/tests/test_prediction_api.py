from fastapi.testclient import TestClient
import pytest

from app.main import app


client = TestClient(app)


def sample_request():
    return {
        "changeSnapshot": {
            "pullRequestNumber": 1,
            "owner": "releaseguard",
            "repository": "demo",
            "title": "Update API",
            "sourceBranch": "feature/demo",
            "targetBranch": "main",
            "headSha": "abc123",
            "changedFiles": [
                {
                    "filename": "src/api/UserService.java",
                    "status": "modified",
                    "additions": 20,
                    "deletions": 5,
                    "changes": 25,
                    "patch": None,
                }
            ],
            "totalAdditions": 20,
            "totalDeletions": 5,
            "totalChanges": 25,
        },
        "findings": [
            {
                "analyzerType": "CODE",
                "findingType": "SECURITY",
                "severity": "HIGH",
                "ruleId": "SEC-001",
                "title": "High severity finding",
                "message": "Synthetic integration-test finding",
                "filePath": "src/api/UserService.java",
                "lineNumber": 42,
            },
            {
                "analyzerType": "DEPENDENCY",
                "findingType": "DEPENDENCY_RISK",
                "severity": "MEDIUM",
                "ruleId": "DEP-001",
                "title": "Dependency finding",
                "message": "Synthetic integration-test finding",
            },
        ],
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "UP"
    assert body["model_name"] in {"xgboost", "xgboost_candidate"}
    assert body["model_version"] in {"1.0.0", "2.0.0"}
    assert body["feature_version"] == "1.0.0"
    assert body["dataset_version"] in {"1.0.0", "2.0.0"}


def test_prediction_endpoint_returns_risk_prediction():
    response = client.post(
        "/api/v1/predict",
        json=sample_request(),
    )

    print("STATUS:", response.status_code)
    print("BODY:", response.json())

    assert response.status_code == 200

    body = response.json()

    assert body["risk_level"] in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }

    assert 0.0 <= body["risk_score"] <= 100.0

    probabilities = body["class_probabilities"]

    assert set(probabilities) == {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }

    assert sum(probabilities.values()) == pytest.approx(1.0, abs=1e-6)

    assert len(body["feature_vector"]) == 28

    assert body["model_name"] in {"xgboost", "xgboost_candidate"}
    assert body["model_version"] in {"1.0.0", "2.0.0"}
    assert body["feature_version"] == "1.0.0"
    assert body["dataset_version"] in {"1.0.0", "2.0.0"}


def test_prediction_request_validation_rejects_missing_change_snapshot():
    response = client.post(
        "/api/v1/predict",
        json={"findings": []},
    )

    assert response.status_code == 422


def test_prediction_request_validation_rejects_negative_change_counts():
    payload = sample_request()
    payload["changeSnapshot"]["totalChanges"] = -1

    response = client.post(
        "/api/v1/predict",
        json=payload,
    )

    assert response.status_code == 422
