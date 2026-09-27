from pathlib import Path

from app.model.artifact import BaselineArtifactManager
from app.model.baseline import BaselineModelConfig
from app.model.training import train_baseline


ARTIFACT_DIRECTORY = Path(
    "artifacts/models/baseline/1.0.0"
)


def build_training_data():
    """
    Temporary deterministic baseline dataset.

    This dataset is intentionally small and synthetic.
    It exists only to validate the complete baseline
    training and artifact pipeline.

    Production training data must come from the
    versioned dataset preparation pipeline.
    """

    X = [
        [1.0, 0.0, 0.0],
        [1.2, 0.1, 0.0],
        [0.0, 1.0, 0.0],
        [0.1, 1.2, 0.0],
        [0.0, 0.0, 1.0],
        [0.1, 0.0, 1.2],
        [0.8, 0.2, 0.1],
        [0.2, 0.8, 0.1],
    ]

    y = [
        "LOW",
        "LOW",
        "MEDIUM",
        "MEDIUM",
        "HIGH",
        "HIGH",
        "CRITICAL",
        "CRITICAL",
    ]

    return X, y


def main() -> None:
    X, y = build_training_data()

    config = BaselineModelConfig(
        random_state=42,
        max_iter=1000,
    )

    result = train_baseline(
        X,
        y,
        config,
    )

    manager = BaselineArtifactManager()

    artifact_path = manager.save(
        result.model,
        ARTIFACT_DIRECTORY,
    )

    print("Baseline training completed.")
    print(f"Samples: {result.sample_count}")
    print(f"Features: {result.feature_count}")
    print(f"Classes: {result.classes}")
    print(f"Artifact: {artifact_path}")


if __name__ == "__main__":
    main()