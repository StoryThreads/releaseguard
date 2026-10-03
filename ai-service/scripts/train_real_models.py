
"""
ReleaseGuard — Real-Data Model Training
=======================================

V0.5.8.5 — Real-Data Model Training

Trains:
    1. Logistic Regression baseline
    2. Multiclass XGBoost candidate

Input:
    data/real/splits/train.jsonl
    data/real/splits/validation.jsonl
    data/real/splits/test.jsonl

Output:
    data/real/models/2.0.0/
        logistic_regression.joblib
        xgboost.joblib
        model_metadata.json
        evaluation.json
        feature_schema.json

    data/real/manifests/
        real_model_training_manifest.json

Model version:
    2.0.0

Important:
    - No synthetic labels are generated.
    - No oversampling is performed.
    - The repository-isolated split from V0.5.8.4 is preserved.
    - Validation/test sets are never used for fitting.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.preprocessing import StandardScaler

try:
    import xgboost as xgb
except ImportError:
    xgb = None


# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent

if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.model.real_pipelines import (
    LogisticRegressionPipeline,
    XGBoostPipeline,
)

DATA_DIR = AI_SERVICE_DIR / "data" / "real"

SPLIT_DIR = DATA_DIR / "splits"
MODEL_VERSION = "2.0.0"

MODEL_DIR = DATA_DIR / "models" / MODEL_VERSION
MANIFEST_DIR = DATA_DIR / "manifests"

TRAIN_FILE = SPLIT_DIR / "train.jsonl"
VALIDATION_FILE = SPLIT_DIR / "validation.jsonl"
TEST_FILE = SPLIT_DIR / "test.jsonl"

LOGISTIC_ARTIFACT = MODEL_DIR / "logistic_regression.joblib"
XGBOOST_ARTIFACT = MODEL_DIR / "xgboost.joblib"

METADATA_FILE = MODEL_DIR / "model_metadata.json"
EVALUATION_FILE = MODEL_DIR / "evaluation.json"
FEATURE_SCHEMA_FILE = MODEL_DIR / "feature_schema.json"

MANIFEST_FILE = MANIFEST_DIR / "real_model_training_manifest.json"

FEATURE_VERSION = "1.0.0"

LABELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
LABEL_TO_ID = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}
ID_TO_LABEL = {v: k for k, v in LABEL_TO_ID.items()}


# ============================================================================
# HELPERS
# ============================================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def ensure_paths() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Required dataset not found: {path}")

    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in {path} at line {line_number}: {exc}"
                ) from exc

            if not isinstance(record, dict):
                raise ValueError(
                    f"Expected JSON object in {path} at line {line_number}"
                )

            records.append(record)

    return records


def get_label(record: dict[str, Any]) -> str:
    """
    Supports the label structures produced by the previous pipeline.
    """

    candidates = [
        record.get("label"),
        record.get("outcome_label"),
        record.get("target"),
        record.get("y"),
    ]

    outcome = record.get("outcome")

    if isinstance(outcome, dict):
        candidates.append(outcome.get("label"))

    metadata = record.get("metadata")

    if isinstance(metadata, dict):
        candidates.append(metadata.get("label"))

    for candidate in candidates:
        if isinstance(candidate, str):
            value = candidate.strip().upper()

            if value in LABEL_TO_ID:
                return value

    raise ValueError(
        f"Could not determine valid label from record: "
        f"{record.get('pull_request', record.get('pr', 'unknown'))}"
    )


def get_pr_identity(record: dict[str, Any]) -> str:
    """
    Extract a stable PR identity.

    Supports the ChangeSnapshot / feature dataset formats.
    """

    candidates = [
        record.get("pr_identity"),
        record.get("pull_request_identity"),
        record.get("identity"),
    ]

    pull_request = record.get("pull_request")

    if isinstance(pull_request, dict):
        repository = pull_request.get("repository")
        number = pull_request.get("number")

        if repository is not None and number is not None:
            return f"{repository}#{number}"

    repository = record.get("repository")
    number = record.get("number")

    if repository is not None and number is not None:
        return f"{repository}#{number}"

    for candidate in candidates:
        if candidate:
            return str(candidate)

    return "UNKNOWN"


def extract_repository(record: dict[str, Any]) -> str:
    pull_request = record.get("pull_request")

    if isinstance(pull_request, dict):
        repository = pull_request.get("repository")

        if repository:
            return str(repository)

    repository = record.get("repository")

    if repository:
        return str(repository)

    return "UNKNOWN"


def extract_feature_mapping(record: dict[str, Any]) -> dict[str, float]:
    """
    Locate the normalized feature vector.

    The feature-generation pipeline can store the vector under several
    reasonable keys. We intentionally support the common structures rather
    than depending on one fragile nesting level.
    """

    candidates: list[Any] = [
        record.get("features"),
        record.get("normalized_features"),
        record.get("feature_vector"),
        record.get("vector"),
    ]

    feature_block = record.get("feature")

    if isinstance(feature_block, dict):
        candidates.extend(
            [
                feature_block.get("features"),
                feature_block.get("normalized"),
                feature_block.get("normalized_features"),
                feature_block.get("vector"),
            ]
        )

    for candidate in candidates:
        if isinstance(candidate, dict):
            numeric: dict[str, float] = {}

            for key, value in candidate.items():
                if isinstance(value, bool):
                    numeric[str(key)] = float(value)

                elif isinstance(value, (int, float)):
                    if np.isfinite(float(value)):
                        numeric[str(key)] = float(value)

            if numeric:
                return numeric

    # Some datasets store:
    #
    # {
    #   "feature_vector": {
    #       "values": {...}
    #   }
    # }
    feature_vector = record.get("feature_vector")

    if isinstance(feature_vector, dict):
        values = feature_vector.get("values")

        if isinstance(values, dict):
            numeric = {}

            for key, value in values.items():
                if isinstance(value, bool):
                    numeric[str(key)] = float(value)

                elif isinstance(value, (int, float)):
                    if np.isfinite(float(value)):
                        numeric[str(key)] = float(value)

            if numeric:
                return numeric

    raise ValueError(
        f"No numeric feature vector found for PR {get_pr_identity(record)}"
    )


def build_feature_matrix(
    records: list[dict[str, Any]],
    feature_names: list[str] | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    """
    Converts JSONL feature records into X/y.

    Missing features are filled with zero.

    This is safe only because the feature schema is already frozen by
    V0.5.8.3. Feature names are taken from the training dataset.
    """

    mappings: list[dict[str, float]] = []
    labels: list[int] = []
    identities: list[str] = []

    for record in records:
        mapping = extract_feature_mapping(record)
        label = get_label(record)

        mappings.append(mapping)
        labels.append(LABEL_TO_ID[label])
        identities.append(get_pr_identity(record))

    if feature_names is None:
        names = set()

        for mapping in mappings:
            names.update(mapping.keys())

        feature_names = sorted(names)

    X = np.zeros(
        (len(records), len(feature_names)),
        dtype=np.float64,
    )

    for row_index, mapping in enumerate(mappings):
        for column_index, feature_name in enumerate(feature_names):
            value = mapping.get(feature_name, 0.0)

            if not np.isfinite(value):
                value = 0.0

            X[row_index, column_index] = value

    y = np.asarray(labels, dtype=np.int64)

    return X, y, feature_names, identities


def label_distribution(y: np.ndarray) -> dict[str, int]:
    counts = Counter(int(value) for value in y)

    return {
        label: int(counts.get(index, 0))
        for index, label in ID_TO_LABEL.items()
    }


def validate_dataset(
    name: str,
    X: np.ndarray,
    y: np.ndarray,
) -> None:
    if len(X) == 0:
        raise ValueError(f"{name} dataset is empty.")

    if len(X) != len(y):
        raise ValueError(
            f"{name} X/y size mismatch: {len(X)} != {len(y)}"
        )

    if not np.isfinite(X).all():
        raise ValueError(
            f"{name} contains NaN or infinite feature values."
        )

    print(f"{name}:")
    print(f"  records : {len(X)}")
    print(f"  features: {X.shape[1]}")

    distribution = label_distribution(y)

    for label in LABELS:
        print(f"  {label:<9}: {distribution[label]}")


def calculate_class_weights(y: np.ndarray) -> dict[int, float]:
    """
    Balanced class weights.

    No samples are duplicated or synthetically generated.
    """

    counts = Counter(int(value) for value in y)

    total = len(y)
    classes = sorted(counts.keys())

    if not classes:
        return {}

    return {
        class_id: total / (len(classes) * counts[class_id])
        for class_id in classes
    }


def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, Any]:
    return {
        "accuracy": float(
            accuracy_score(y_true, y_pred)
        ),
        "macro_f1": float(
            f1_score(
                y_true,
                y_pred,
                labels=list(range(len(LABELS))),
                average="macro",
                zero_division=0,
            )
        ),
        "weighted_f1": float(
            f1_score(
                y_true,
                y_pred,
                labels=list(range(len(LABELS))),
                average="weighted",
                zero_division=0,
            )
        ),
        "macro_precision": float(
            precision_score(
                y_true,
                y_pred,
                labels=list(range(len(LABELS))),
                average="macro",
                zero_division=0,
            )
        ),
        "macro_recall": float(
            recall_score(
                y_true,
                y_pred,
                labels=list(range(len(LABELS))),
                average="macro",
                zero_division=0,
            )
        ),
        "confusion_matrix": confusion_matrix(
            y_true,
            y_pred,
            labels=list(range(len(LABELS))),
        ).tolist(),
        "labels": LABELS,
    }


def evaluate_model(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
) -> dict[str, Any]:
    predictions = model.predict(X)

    predictions = np.asarray(predictions, dtype=np.int64)

    return calculate_metrics(y, predictions)


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            payload,
            handle,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )

        handle.write("\n")


# ============================================================================
# LOGISTIC REGRESSION
# ============================================================================

def train_logistic_regression(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> tuple[Any, StandardScaler]:
    print()
    print("Training Logistic Regression...")

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(X_train)

    class_weights = calculate_class_weights(y_train)

    model = LogisticRegression(
        multi_class="auto",
        class_weight=class_weights if class_weights else "balanced",
        max_iter=5000,
        random_state=42,
        solver="lbfgs",
    )

    model.fit(X_train_scaled, y_train)

    return model, scaler


# ============================================================================
# XGBOOST
# ============================================================================

def train_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> XGBoostPipeline:
    if xgb is None:
        raise ImportError(
            "xgboost is not installed. "
            "Install it with: pip install xgboost"
        )

    print()
    print("Training multiclass XGBoost...")

    unique_classes = np.unique(y_train)

    if len(unique_classes) < 2:
        raise ValueError(
            "XGBoost requires at least two classes in the training set. "
            f"Found: {unique_classes.tolist()}"
        )

    class_to_index = {
        int(cls): idx
        for idx, cls in enumerate(unique_classes)
    }

    encoded_y = np.asarray(
        [class_to_index[int(y)] for y in y_train],
        dtype=np.int64,
    )

    class_weights = calculate_class_weights(y_train)

    sample_weights = np.asarray(
        [
            class_weights.get(int(label), 1.0)
            for label in y_train
        ],
        dtype=np.float64,
    )

    model = xgb.XGBClassifier(
        objective="multi:softprob",
        num_class=len(unique_classes),
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        reg_alpha=0.0,
        reg_lambda=1.0,
        min_child_weight=1,
        random_state=42,
        eval_metric="mlogloss",
        tree_method="hist",
        n_jobs=-1,
    )

    model.fit(
        X_train,
        encoded_y,
        sample_weight=sample_weights,
        verbose=False,
    )

    return XGBoostPipeline(
        model=model,
        classes=unique_classes,
    )


# ============================================================================
# MAIN
# ============================================================================

def train_models() -> None:
    print("=" * 70)
    print("ReleaseGuard — Real-Data Model Training")
    print("=" * 70)

    print(f"Model version : {MODEL_VERSION}")
    print(f"Feature version: {FEATURE_VERSION}")

    ensure_paths()

    # ---------------------------------------------------------------------
    # Load datasets
    # ---------------------------------------------------------------------

    print()
    print("Loading split datasets...")

    train_records = load_jsonl(TRAIN_FILE)
    validation_records = load_jsonl(VALIDATION_FILE)
    test_records = load_jsonl(TEST_FILE)

    print(f"Train records      : {len(train_records)}")
    print(f"Validation records : {len(validation_records)}")
    print(f"Test records       : {len(test_records)}")

    # ---------------------------------------------------------------------
    # Build feature matrices
    # ---------------------------------------------------------------------

    print()
    print("Extracting feature matrices...")

    X_train, y_train, feature_names, train_ids = build_feature_matrix(
        train_records
    )

    X_validation, y_validation, _, validation_ids = build_feature_matrix(
        validation_records,
        feature_names,
    )

    X_test, y_test, _, test_ids = build_feature_matrix(
        test_records,
        feature_names,
    )

    # ---------------------------------------------------------------------
    # Validate
    # ---------------------------------------------------------------------

    print()
    validate_dataset(
        "TRAIN",
        X_train,
        y_train,
    )

    validate_dataset(
        "VALIDATION",
        X_validation,
        y_validation,
    )

    validate_dataset(
        "TEST",
        X_test,
        y_test,
    )

    unique_train_classes = sorted(
        set(int(value) for value in y_train)
    )

    print()
    print("Training classes:")

    for class_id in unique_train_classes:
        print(
            f"  {class_id}: {ID_TO_LABEL[class_id]}"
        )

    if len(unique_train_classes) < 2:
        raise RuntimeError(
            "\n"
            "TRAINING BLOCKED\n"
            "----------------\n"
            "The repository-isolated training split contains fewer "
            "than two classes.\n\n"
            f"Training labels: "
            f"{[ID_TO_LABEL[x] for x in unique_train_classes]}\n\n"
            "A classifier cannot be legitimately trained from this split.\n"
            "Do NOT train on validation/test data and do NOT create "
            "synthetic labels.\n\n"
            "The V0.5.8.4 repository split must be revised so that "
            "the training repositories contain sufficient outcome "
            "classes."
        )

    # ---------------------------------------------------------------------
    # Train Logistic Regression
    # ---------------------------------------------------------------------

    logistic_model, scaler = train_logistic_regression(
        X_train,
        y_train,
    )

    logistic_pipeline = LogisticRegressionPipeline(
        scaler=scaler,
        model=logistic_model,
    )

    # ---------------------------------------------------------------------
    # Train XGBoost
    # ---------------------------------------------------------------------

    xgb_model = train_xgboost(
        X_train,
        y_train,
    )

    # ---------------------------------------------------------------------
    # Evaluate
    # ---------------------------------------------------------------------

    print()
    print("Evaluating Logistic Regression...")

    logistic_validation_metrics = evaluate_model(
        logistic_pipeline,
        X_validation,
        y_validation,
    )

    logistic_test_metrics = evaluate_model(
        logistic_pipeline,
        X_test,
        y_test,
    )

    print()
    print("Evaluating XGBoost...")

    xgb_validation_metrics = evaluate_model(
        xgb_model,
        X_validation,
        y_validation,
    )

    xgb_test_metrics = evaluate_model(
        xgb_model,
        X_test,
        y_test,
    )

    # ---------------------------------------------------------------------
    # Save artifacts
    # ---------------------------------------------------------------------

    print()
    print("Saving versioned model artifacts...")

    joblib.dump(
        logistic_pipeline,
        LOGISTIC_ARTIFACT,
    )

    joblib.dump(
        xgb_model,
        XGBOOST_ARTIFACT,
    )

    # ---------------------------------------------------------------------
    # Feature schema
    # ---------------------------------------------------------------------

    feature_schema = {
        "schema_version": "1.0.0",
        "feature_version": FEATURE_VERSION,
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "label_mapping": LABEL_TO_ID,
        "model_version": MODEL_VERSION,
    }

    write_json(
        FEATURE_SCHEMA_FILE,
        feature_schema,
    )

    # ---------------------------------------------------------------------
    # Evaluation
    # ---------------------------------------------------------------------

    evaluation = {
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "created_at_utc": utc_now(),
        "protocol": {
            "metrics": [
                "accuracy",
                "macro_f1",
                "weighted_f1",
                "macro_precision",
                "macro_recall",
                "confusion_matrix",
            ],
            "labels": LABELS,
            "label_mapping": LABEL_TO_ID,
            "class_weighting": "balanced",
            "oversampling": False,
            "synthetic_labels": False,
        },
        "logistic_regression": {
            "validation": logistic_validation_metrics,
            "test": logistic_test_metrics,
        },
        "xgboost": {
            "validation": xgb_validation_metrics,
            "test": xgb_test_metrics,
        },
    }

    write_json(
        EVALUATION_FILE,
        evaluation,
    )

    # ---------------------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------------------

    metadata = {
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "created_at_utc": utc_now(),
        "training_environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "xgboost": (
                xgb.__version__
                if xgb is not None
                else None
            ),
        },
        "dataset": {
            "train_file": str(TRAIN_FILE),
            "validation_file": str(VALIDATION_FILE),
            "test_file": str(TEST_FILE),
            "train_records": len(train_records),
            "validation_records": len(validation_records),
            "test_records": len(test_records),
        },
        "features": {
            "feature_version": FEATURE_VERSION,
            "feature_count": len(feature_names),
            "feature_names": feature_names,
        },
        "labels": {
            "classes": LABELS,
            "mapping": LABEL_TO_ID,
            "train_distribution": label_distribution(y_train),
            "validation_distribution": label_distribution(
                y_validation
            ),
            "test_distribution": label_distribution(y_test),
        },
        "models": {
            "logistic_regression": {
                "artifact": str(LOGISTIC_ARTIFACT),
                "algorithm": "LogisticRegression",
                "solver": "lbfgs",
                "max_iter": 5000,
                "class_weight": "balanced",
                "random_state": 42,
            },
            "xgboost": {
                "artifact": str(XGBOOST_ARTIFACT),
                "algorithm": "XGBClassifier",
                "objective": "multi:softprob",
                "n_estimators": 300,
                "max_depth": 5,
                "learning_rate": 0.05,
                "subsample": 0.85,
                "colsample_bytree": 0.85,
                "random_state": 42,
            },
        },
        "protocol": {
            "repository_isolated_split": True,
            "temporal_policy_from_v0_5_8_4": True,
            "oversampling": False,
            "synthetic_labels": False,
            "evaluation": [
                "accuracy",
                "macro_f1",
                "weighted_f1",
                "macro_precision",
                "macro_recall",
                "confusion_matrix",
            ],
        },
    }

    write_json(
        METADATA_FILE,
        metadata,
    )

    # ---------------------------------------------------------------------
    # Reproducibility hashes
    # ---------------------------------------------------------------------

    manifest = {
        "schema_version": "1.0.0",
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "created_at_utc": utc_now(),
        "source_dataset_version": "2.0.1",
        "inputs": {
            "train": {
                "path": str(TRAIN_FILE),
                "sha256": sha256_file(TRAIN_FILE),
                "records": len(train_records),
            },
            "validation": {
                "path": str(VALIDATION_FILE),
                "sha256": sha256_file(VALIDATION_FILE),
                "records": len(validation_records),
            },
            "test": {
                "path": str(TEST_FILE),
                "sha256": sha256_file(TEST_FILE),
                "records": len(test_records),
            },
        },
        "outputs": {
            "logistic_regression": {
                "path": str(LOGISTIC_ARTIFACT),
                "sha256": sha256_file(LOGISTIC_ARTIFACT),
            },
            "xgboost": {
                "path": str(XGBOOST_ARTIFACT),
                "sha256": sha256_file(XGBOOST_ARTIFACT),
            },
            "metadata": {
                "path": str(METADATA_FILE),
                "sha256": sha256_file(METADATA_FILE),
            },
            "evaluation": {
                "path": str(EVALUATION_FILE),
                "sha256": sha256_file(EVALUATION_FILE),
            },
            "feature_schema": {
                "path": str(FEATURE_SCHEMA_FILE),
                "sha256": sha256_file(FEATURE_SCHEMA_FILE),
            },
        },
        "records": {
            "train": len(train_records),
            "validation": len(validation_records),
            "test": len(test_records),
            "features": len(feature_names),
        },
        "label_distribution": {
            "train": label_distribution(y_train),
            "validation": label_distribution(y_validation),
            "test": label_distribution(y_test),
        },
        "training": {
            "logistic_regression": "COMPLETED",
            "xgboost": "COMPLETED",
            "model_artifacts": "VERSIONED",
            "model_metadata": "RECORDED",
            "evaluation_protocol": "V0.5_COMPATIBLE",
            "model_version": MODEL_VERSION,
        },
    }

    write_json(
        MANIFEST_FILE,
        manifest,
    )

    # ---------------------------------------------------------------------
    # Console summary
    # ---------------------------------------------------------------------

    print()
    print("=" * 70)
    print("REAL-DATA MODEL TRAINING COMPLETE")
    print("=" * 70)

    print(f"Model version : {MODEL_VERSION}")
    print(f"Feature version: {FEATURE_VERSION}")

    print()
    print("Training records:")
    print(f"  Train      : {len(train_records)}")
    print(f"  Validation : {len(validation_records)}")
    print(f"  Test       : {len(test_records)}")

    print()
    print("Feature count:")
    print(f"  {len(feature_names)}")

    print()
    print("Logistic Regression — Test")
    print(
        f"  Accuracy        : "
        f"{logistic_test_metrics['accuracy']:.4f}"
    )
    print(
        f"  Macro F1        : "
        f"{logistic_test_metrics['macro_f1']:.4f}"
    )
    print(
        f"  Weighted F1     : "
        f"{logistic_test_metrics['weighted_f1']:.4f}"
    )
    print(
        f"  Macro Precision : "
        f"{logistic_test_metrics['macro_precision']:.4f}"
    )
    print(
        f"  Macro Recall    : "
        f"{logistic_test_metrics['macro_recall']:.4f}"
    )

    print()
    print("XGBoost — Test")
    print(
        f"  Accuracy        : "
        f"{xgb_test_metrics['accuracy']:.4f}"
    )
    print(
        f"  Macro F1        : "
        f"{xgb_test_metrics['macro_f1']:.4f}"
    )
    print(
        f"  Weighted F1     : "
        f"{xgb_test_metrics['weighted_f1']:.4f}"
    )
    print(
        f"  Macro Precision : "
        f"{xgb_test_metrics['macro_precision']:.4f}"
    )
    print(
        f"  Macro Recall    : "
        f"{xgb_test_metrics['macro_recall']:.4f}"
    )

    print()
    print("Artifacts:")
    print(f"  Logistic Regression : {LOGISTIC_ARTIFACT}")
    print(f"  XGBoost             : {XGBOOST_ARTIFACT}")
    print(f"  Metadata            : {METADATA_FILE}")
    print(f"  Evaluation          : {EVALUATION_FILE}")
    print(f"  Feature schema      : {FEATURE_SCHEMA_FILE}")
    print(f"  Manifest            : {MANIFEST_FILE}")

    print()
    print("IMPORTANT:")
    print("  Model version 2.0.0 is frozen.")
    print("  No validation/test records were used for fitting.")
    print("  No synthetic labels or oversampling were applied.")
    print("=" * 70)


if __name__ == "__main__":
    try:
        train_models()
    except Exception as exc:
        print()
        print("=" * 70)
        print("REAL-DATA MODEL TRAINING FAILED")
        print("=" * 70)
        print(f"{type(exc).__name__}: {exc}")
        print("=" * 70)
        raise
