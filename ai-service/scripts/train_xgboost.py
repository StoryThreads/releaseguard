import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.model.xgboost_training import train_xgboost_candidate
from app.model.xgboost_artifact import XGBoostArtifactManager


X = [
    [0.10, 0.10],
    [0.15, 0.12],
    [0.20, 0.18],
    [0.25, 0.20],
    [0.60, 0.55],
    [0.65, 0.60],
    [0.70, 0.68],
    [0.75, 0.72],
    [0.90, 0.85],
    [0.92, 0.88],
    [0.95, 0.94],
    [0.98, 0.96],
]

y = [
    "LOW",
    "LOW",
    "LOW",
    "LOW",
    "MEDIUM",
    "MEDIUM",
    "MEDIUM",
    "MEDIUM",
    "HIGH",
    "HIGH",
    "CRITICAL",
    "CRITICAL",
]


def main():
    result = train_xgboost_candidate(X, y)

    artifact_directory = (
        PROJECT_ROOT
        / "artifacts"
        / "models"
        / "xgboost"
        / "1.0.0"
    )

    manager = XGBoostArtifactManager()

    artifact_path = manager.save(
        result.model,
        artifact_directory,
    )

    print(f"Model saved to: {artifact_path}")
    print(f"Samples: {result.sample_count}")
    print(f"Features: {result.feature_count}")
    print(f"Classes: {result.classes}")


if __name__ == "__main__":
    main()