import random
import sys
from dataclasses import fields
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.features.extractor import FeatureExtractor
from app.features.input_mapper import InputMapper
from app.features.normalizer import FeatureNormalizer
from app.model.xgboost_artifact import XGBoostArtifactManager
from app.model.xgboost_training import train_xgboost_candidate


ARTIFACT_DIRECTORY = (
    PROJECT_ROOT / "artifacts" / "models" / "xgboost" / "1.0.0"
)

LABELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def build_training_data():
    """
    Deterministic synthetic development data.

    This is NOT production training data. It exists to produce an
    artifact that is structurally compatible with Feature Schema 1.0.0
    and the V0.5.7 prediction service.

    Production training must consume the approved V0.5.2 dataset.
    """
    rng = random.Random(42)
    extractor = FeatureExtractor()
    normalizer = FeatureNormalizer()

    X = []
    y = []

    for label in LABELS:
        for _ in range(30):
            severity_count = {
                "LOW": {"LOW": rng.randint(0, 3), "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
                "MEDIUM": {"LOW": rng.randint(0, 2), "MEDIUM": rng.randint(1, 4), "HIGH": 0, "CRITICAL": 0},
                "HIGH": {"LOW": rng.randint(0, 2), "MEDIUM": rng.randint(0, 2), "HIGH": rng.randint(1, 4), "CRITICAL": 0},
                "CRITICAL": {"LOW": rng.randint(0, 2), "MEDIUM": rng.randint(0, 2), "HIGH": rng.randint(1, 3), "CRITICAL": rng.randint(1, 3)},
            }[label]

            file_count = {
                "LOW": rng.randint(1, 4),
                "MEDIUM": rng.randint(2, 8),
                "HIGH": rng.randint(4, 15),
                "CRITICAL": rng.randint(5, 20),
            }[label]

            additions = {
                "LOW": rng.randint(1, 30),
                "MEDIUM": rng.randint(20, 100),
                "HIGH": rng.randint(60, 250),
                "CRITICAL": rng.randint(120, 500),
            }[label]

            deletions = rng.randint(0, max(1, additions // 3))
            total_changes = additions + deletions

            changed_files = []
            for index in range(file_count):
                status = rng.choice(["modified", "added"])
                changed_files.append({
                    "filename": f"src/file_{index}.java",
                    "status": status,
                    "additions": max(0, additions // file_count),
                    "deletions": max(0, deletions // file_count),
                    "changes": max(0, total_changes // file_count),
                })

            findings = []
            analyzer_types = ["CODE", "DEPENDENCY", "API", "DATABASE", "TEST_IMPACT"]
            for severity, count in severity_count.items():
                for index in range(count):
                    findings.append({
                        "analyzerType": rng.choice(analyzer_types),
                        "findingType": "SYNTHETIC",
                        "severity": severity,
                        "ruleId": f"SYN-{severity}-{index}",
                    })

            raw = {
                "changeSnapshot": {
                    "pullRequestNumber": 1,
                    "owner": "synthetic",
                    "repository": "releaseguard",
                    "title": f"Synthetic {label} sample",
                    "sourceBranch": "synthetic",
                    "targetBranch": "main",
                    "headSha": "synthetic",
                    "changedFiles": changed_files,
                    "totalAdditions": additions,
                    "totalDeletions": deletions,
                    "totalChanges": total_changes,
                },
                "findings": findings,
            }

            internal = InputMapper.from_dict(raw)
            feature_vector = extractor.extract(internal)
            normalized = normalizer.normalize(feature_vector)

            X.append([
                float(getattr(normalized, field.name))
                for field in fields(normalized)
            ])
            y.append(label)

    return X, y


def main():
    X, y = build_training_data()

    result = train_xgboost_candidate(X, y)

    manager = XGBoostArtifactManager()
    artifact_path = manager.save(
        result.model,
        ARTIFACT_DIRECTORY,
    )

    print("XGBoost training completed.")
    print(f"Samples: {result.sample_count}")
    print(f"Features: {result.feature_count}")
    print(f"Classes: {result.classes}")
    print(f"Artifact: {artifact_path}")


if __name__ == "__main__":
    main()
