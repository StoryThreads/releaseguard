import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.model.artifact import BaselineArtifactManager
from app.model.baseline import LogisticRegressionBaseline
from train_xgboost import build_training_data


ARTIFACT_DIRECTORY = (
    PROJECT_ROOT / "artifacts" / "models" / "baseline" / "1.0.0"
)


def main() -> None:
    X, y = build_training_data()

    model = LogisticRegressionBaseline()
    model.fit(X, y)

    manager = BaselineArtifactManager()
    artifact_path = manager.save(
        model,
        ARTIFACT_DIRECTORY,
    )

    print("Logistic Regression baseline training completed.")
    print(f"Samples: {len(X)}")
    print(f"Features: {len(X[0]) if X else 0}")
    print(f"Classes: {model.classes}")
    print(f"Artifact: {artifact_path}")


if __name__ == "__main__":
    main()
