# ai-service/scripts/evaluate_real_models.py

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
)


# ============================================================================
# PATHS / VERSIONING
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent

if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))

from app.model.real_pipelines import (
    LogisticRegressionPipeline,
    XGBoostPipeline,
)

sys.modules.setdefault("__main__", sys.modules[__name__])
setattr(sys.modules["__main__"], "LogisticRegressionPipeline", LogisticRegressionPipeline)
setattr(sys.modules["__main__"], "XGBoostPipeline", XGBoostPipeline)

DATA_DIR = AI_SERVICE_DIR / "data"

REAL_DIR = DATA_DIR / "real"
MODEL_VERSION = os.getenv("MODEL_VERSION", "2.0.0")
FEATURE_VERSION = "1.0.0"

REAL_SPLIT_DIR = REAL_DIR / "splits"
REAL_MODEL_DIR = REAL_DIR / "models" / MODEL_VERSION

OUTPUT_DIR = REAL_DIR / "evaluation"
MANIFEST_DIR = REAL_DIR / "manifests"

TRAIN_FILE = REAL_SPLIT_DIR / "train.jsonl"
VALIDATION_FILE = REAL_SPLIT_DIR / "validation.jsonl"
TEST_FILE = REAL_SPLIT_DIR / "test.jsonl"

LOGISTIC_MODEL_FILE = REAL_MODEL_DIR / "logistic_regression.joblib"
XGBOOST_MODEL_FILE = REAL_MODEL_DIR / "xgboost.joblib"

MODEL_METADATA_FILE = REAL_MODEL_DIR / "model_metadata.json"
TRAINING_EVALUATION_FILE = REAL_MODEL_DIR / "evaluation.json"
FEATURE_SCHEMA_FILE = REAL_MODEL_DIR / "feature_schema.json"

OUTPUT_FILE = OUTPUT_DIR / "real_model_evaluation.json"
MANIFEST_FILE = MANIFEST_DIR / "real_model_evaluation_manifest.json"

CLASS_NAMES = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]

CLASS_TO_ID = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2,
    "CRITICAL": 3,
}

ID_TO_CLASS = {
    value: key
    for key, value in CLASS_TO_ID.items()
}


# ============================================================================
# OPTIONAL SYNTHETIC BASELINE DISCOVERY
# ============================================================================

SYNTHETIC_BASELINE_CANDIDATES = [
    # Common locations inside this project.
    DATA_DIR / "synthetic" / "evaluation.json",
    DATA_DIR / "synthetic" / "models" / "evaluation.json",
    DATA_DIR / "models" / "evaluation.json",
    DATA_DIR / "evaluation.json",

    # V0.5 style model locations.
    DATA_DIR / "models" / "baseline" / "evaluation.json",
    DATA_DIR / "models" / "xgboost" / "evaluation.json",

    # Repository-level locations.
    AI_SERVICE_DIR / "models" / "evaluation.json",
    AI_SERVICE_DIR / "evaluation.json",
]


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


def require_file(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Required {description} not found:\n  {path}"
        )


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []

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


def first_present(
    record: Dict[str, Any],
    paths: List[Tuple[str, ...]],
) -> Any:
    for path in paths:
        current: Any = record

        try:
            for key in path:
                if not isinstance(current, dict):
                    raise KeyError(key)

                current = current[key]

            if current is not None:
                return current

        except KeyError:
            continue

    return None


def normalize_label(value: Any) -> str:
    if isinstance(value, str):
        label = value.strip().upper()

        if label in CLASS_TO_ID:
            return label

    if isinstance(value, (int, np.integer)):
        value = int(value)

        if value in ID_TO_CLASS:
            return ID_TO_CLASS[value]

    raise ValueError(f"Unsupported label value: {value!r}")


def extract_label(record: Dict[str, Any]) -> str:
    value = first_present(
        record,
        [
            ("label",),
            ("outcome", "label"),
            ("target",),
            ("y",),
            ("class",),
        ],
    )

    if value is None:
        raise ValueError(
            "Could not determine label from feature record. "
            f"Available keys: {list(record.keys())}"
        )

    return normalize_label(value)


def extract_feature_vector(record: Dict[str, Any]) -> List[float]:
    """
    Supports the feature structures produced by the ReleaseGuard feature
    generation pipeline.

    Accepted forms:

      {
        "features": {
            "feature_name": 1.0,
            ...
        }
      }

    or:

      {
        "feature_vector": [...]
      }

    or:

      {
        "features": [...]
      }

    or:

      {
        "feature_values": [...]
      }
    """

    value = first_present(
        record,
        [
            ("feature_vector",),
            ("features",),
            ("feature_values",),
        ],
    )

    if value is None:
        raise ValueError(
            "Could not find feature vector in record. "
            f"Available keys: {list(record.keys())}"
        )

    if isinstance(value, dict):
        values: List[float] = []

        # Preserve JSON insertion order.
        for key, item in value.items():
            if isinstance(item, bool):
                values.append(float(item))
            elif isinstance(item, (int, float)):
                values.append(float(item))
            else:
                raise ValueError(
                    f"Non-numeric feature '{key}': {item!r}"
                )

        return values

    if isinstance(value, list):
        result: List[float] = []

        for index, item in enumerate(value):
            if isinstance(item, bool):
                result.append(float(item))
            elif isinstance(item, (int, float)):
                result.append(float(item))
            else:
                raise ValueError(
                    f"Non-numeric feature at index {index}: {item!r}"
                )

        return result

    raise ValueError(
        f"Unsupported feature representation: {type(value).__name__}"
    )


def extract_matrix(
    records: List[Dict[str, Any]],
) -> Tuple[np.ndarray, np.ndarray]:
    features: List[List[float]] = []
    labels: List[int] = []

    for index, record in enumerate(records, start=1):
        vector = extract_feature_vector(record)
        label = extract_label(record)

        features.append(vector)
        labels.append(CLASS_TO_ID[label])

    if not features:
        raise ValueError("Feature dataset is empty.")

    feature_count = len(features[0])

    if feature_count == 0:
        raise ValueError("Feature vectors contain zero features.")

    for index, vector in enumerate(features, start=1):
        if len(vector) != feature_count:
            raise ValueError(
                f"Inconsistent feature count at record {index}: "
                f"expected {feature_count}, got {len(vector)}"
            )

    X = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int64)

    if not np.isfinite(X).all():
        raise ValueError("Feature matrix contains NaN or infinite values.")

    return X, y


def class_distribution(y: np.ndarray) -> Dict[str, int]:
    return {
        class_name: int(np.sum(y == class_id))
        for class_name, class_id in CLASS_TO_ID.items()
    }


def safe_divide(numerator: int, denominator: int) -> Optional[float]:
    if denominator == 0:
        return None

    return float(numerator / denominator)


# ============================================================================
# METRICS
# ============================================================================

def evaluate_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, Any]:

    labels = list(CLASS_TO_ID.values())

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=labels,
    )

    precision = precision_score(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )

    macro_f1 = f1_score(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )

    weighted_f1 = f1_score(
        y_true,
        y_pred,
        labels=labels,
        average="weighted",
        zero_division=0,
    )

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0,
    )

    high_id = CLASS_TO_ID["HIGH"]
    critical_id = CLASS_TO_ID["CRITICAL"]

    high_row = report["HIGH"]
    critical_row = report["CRITICAL"]

    high_support = int(high_row["support"])
    critical_support = int(critical_row["support"])

    return {
        "accuracy": float(accuracy),
        "macro_precision": float(precision),
        "macro_recall": float(recall),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),

        "high_recall": (
            float(high_row["recall"])
            if high_support > 0
            else None
        ),

        "critical_recall": (
            float(critical_row["recall"])
            if critical_support > 0
            else None
        ),

        "per_class": {
            class_name: {
                "precision": float(report[class_name]["precision"]),
                "recall": float(report[class_name]["recall"]),
                "f1": float(report[class_name]["f1-score"]),
                "support": int(report[class_name]["support"]),
            }
            for class_name in CLASS_NAMES
        },

        "confusion_matrix": {
            "labels": CLASS_NAMES,
            "matrix": cm.astype(int).tolist(),
        },
    }


# ============================================================================
# PROBABILITY CALIBRATION
# ============================================================================

def evaluate_probability_calibration(
    model: Any,
    X: np.ndarray,
    y_true: np.ndarray,
) -> Dict[str, Any]:

    result: Dict[str, Any] = {
        "applicable": False,
        "reason": None,
    }

    if not hasattr(model, "predict_proba"):
        result["reason"] = (
            "Model does not expose predict_proba()."
        )
        return result

    try:
        probabilities = model.predict_proba(X)
    except Exception as exc:
        result["reason"] = (
            "predict_proba() could not be executed: "
            f"{type(exc).__name__}: {exc}"
        )
        return result

    probabilities = np.asarray(probabilities, dtype=np.float64)

    if probabilities.ndim != 2:
        result["reason"] = (
            f"Expected 2D probability matrix, got shape "
            f"{probabilities.shape}."
        )
        return result

    if not np.isfinite(probabilities).all():
        result["reason"] = "Probability matrix contains NaN or infinite values."
        return result

    row_sums = probabilities.sum(axis=1)

    if not np.allclose(row_sums, 1.0, atol=1e-5):
        result["reason"] = (
            "Predicted probabilities do not sum to 1."
        )
        return result

    # Normalize to exact float64 unit simplex to avoid float32 rounding differences
    safe_row_sums = np.where(row_sums == 0, 1.0, row_sums)[:, np.newaxis]
    probabilities = probabilities / safe_row_sums

    model_classes = getattr(model, "classes_", None)

    if model_classes is None:
        result["reason"] = (
            "Model exposes predict_proba() but not classes_."
        )
        return result

    model_classes = np.asarray(model_classes)

    # The real dataset has four possible classes. A training split may contain
    # fewer classes. Calibration can still be evaluated, but only against the
    # classes actually represented by the model.
    class_ids = [
        int(item)
        for item in model_classes.tolist()
    ]

    valid_class_ids = set(CLASS_TO_ID.values())

    if not set(class_ids).issubset(valid_class_ids):
        result["reason"] = (
            f"Model contains unexpected class IDs: {class_ids}"
        )
        return result

    # Convert y_true into the model's class-index positions.
    class_position = {
        class_id: position
        for position, class_id in enumerate(class_ids)
    }

    if not set(y_true.tolist()).issubset(class_position.keys()):
        result["reason"] = (
            "Evaluation set contains classes that the model cannot predict. "
            f"Model classes: {class_ids}; "
            f"evaluation classes: {sorted(set(y_true.tolist()))}"
        )
        return result

    probability_indices = np.asarray(
        [
            class_position[int(label)]
            for label in y_true
        ],
        dtype=np.int64,
    )

    true_probabilities = probabilities[
        np.arange(len(y_true)),
        probability_indices,
    ]

    # Multiclass Brier score.
    one_hot = np.zeros_like(probabilities)

    for row_index, class_position_index in enumerate(probability_indices):
        one_hot[row_index, class_position_index] = 1.0

    brier_score = float(
        np.mean(
            np.sum(
                (probabilities - one_hot) ** 2,
                axis=1,
            )
        )
    )

    try:
        multiclass_log_loss = float(
            log_loss(
                y_true,
                probabilities,
                labels=model_classes,
            )
        )
    except Exception:
        multiclass_log_loss = None

    # Simple confidence/reliability statistics.
    predicted_class_positions = np.argmax(
        probabilities,
        axis=1,
    )

    predicted_class_ids = model_classes[predicted_class_positions]

    correct = predicted_class_ids == y_true

    confidence = np.max(
        probabilities,
        axis=1,
    )

    result.update(
        {
            "applicable": True,
            "reason": None,
            "model_classes": [
                ID_TO_CLASS[int(class_id)]
                for class_id in model_classes
            ],
            "multiclass_brier_score": brier_score,
            "multiclass_log_loss": multiclass_log_loss,
            "mean_predicted_confidence": float(
                np.mean(confidence)
            ),
            "mean_confidence_correct": (
                float(np.mean(confidence[correct]))
                if np.any(correct)
                else None
            ),
            "mean_confidence_incorrect": (
                float(np.mean(confidence[~correct]))
                if np.any(~correct)
                else None
            ),
            "mean_true_class_probability": float(
                np.mean(true_probabilities)
            ),
        }
    )

    return result


# ============================================================================
# MODEL EVALUATION
# ============================================================================

def evaluate_model(
    model_name: str,
    model_path: Path,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> Dict[str, Any]:

    require_file(
        model_path,
        f"{model_name} model artifact",
    )

    print(f"\nEvaluating {model_name}...")
    print(f"  Artifact: {model_path}")

    model = joblib.load(model_path)

    y_pred = np.asarray(
        model.predict(X_test),
        dtype=np.int64,
    )

    prediction_metrics = evaluate_predictions(
        y_test,
        y_pred,
    )

    calibration = evaluate_probability_calibration(
        model,
        X_test,
        y_test,
    )

    result = {
        "model_name": model_name,
        "artifact": str(model_path),
        "artifact_sha256": sha256_file(model_path),
        "metrics": prediction_metrics,
        "probability_calibration": calibration,
    }

    print(
        f"  Accuracy        : "
        f"{prediction_metrics['accuracy']:.4f}"
    )
    print(
        f"  Macro F1        : "
        f"{prediction_metrics['macro_f1']:.4f}"
    )
    print(
        f"  Weighted F1     : "
        f"{prediction_metrics['weighted_f1']:.4f}"
    )
    print(
        f"  Macro Precision : "
        f"{prediction_metrics['macro_precision']:.4f}"
    )
    print(
        f"  Macro Recall    : "
        f"{prediction_metrics['macro_recall']:.4f}"
    )

    high_recall = prediction_metrics["high_recall"]
    critical_recall = prediction_metrics["critical_recall"]

    print(
        "  HIGH Recall     : "
        + (
            f"{high_recall:.4f}"
            if high_recall is not None
            else "N/A"
        )
    )

    print(
        "  CRITICAL Recall : "
        + (
            f"{critical_recall:.4f}"
            if critical_recall is not None
            else "N/A"
        )
    )

    if calibration["applicable"]:
        print(
            f"  Brier Score     : "
            f"{calibration['multiclass_brier_score']:.6f}"
        )

        if calibration["multiclass_log_loss"] is not None:
            print(
                f"  Log Loss        : "
                f"{calibration['multiclass_log_loss']:.6f}"
            )
    else:
        print(
            "  Calibration     : "
            f"NOT AVAILABLE ({calibration['reason']})"
        )

    return result


# ============================================================================
# SYNTHETIC BASELINE
# ============================================================================

def find_synthetic_baseline() -> Optional[Path]:
    for candidate in SYNTHETIC_BASELINE_CANDIDATES:
        if candidate.exists() and candidate.is_file():
            return candidate

    # Conservative recursive discovery.
    # We only search known evaluation filenames, avoiding arbitrary files.
    search_roots = [
        DATA_DIR / "models",
        DATA_DIR / "synthetic",
        AI_SERVICE_DIR / "models",
    ]

    seen: set[Path] = set()

    for root in search_roots:
        if not root.exists():
            continue

        for path in root.rglob("evaluation.json"):
            resolved = path.resolve()

            if resolved in seen:
                continue

            seen.add(resolved)

            # Do not accidentally select the real-data training evaluation.
            if REAL_MODEL_DIR.resolve() in resolved.parents:
                continue

            return path

    return None


def load_synthetic_baseline() -> Dict[str, Any]:
    path = find_synthetic_baseline()

    if path is None:
        return {
            "available": False,
            "reason": (
                "No synthetic-data evaluation artifact was found in the "
                "known project locations. No synthetic baseline was invented "
                "or reconstructed."
            ),
        }

    try:
        data = load_json(path)
    except Exception as exc:
        return {
            "available": False,
            "path": str(path),
            "reason": (
                f"Could not read synthetic evaluation artifact: "
                f"{type(exc).__name__}: {exc}"
            ),
        }

    return {
        "available": True,
        "path": str(path),
        "sha256": sha256_file(path),
        "evaluation": data,
    }


def compare_against_synthetic(
    real_models: Dict[str, Any],
    synthetic_baseline: Dict[str, Any],
) -> Dict[str, Any]:

    if not synthetic_baseline.get("available"):
        return {
            "performed": False,
            "reason": synthetic_baseline.get("reason"),
        }

    baseline = synthetic_baseline.get("evaluation")

    if not isinstance(baseline, dict):
        return {
            "performed": False,
            "reason": (
                "Synthetic baseline evaluation artifact is not a JSON object."
            ),
        }

    comparisons: Dict[str, Any] = {}

    # The exact structure of the old synthetic evaluation may differ from
    # the real-data evaluation structure. We therefore only compare metrics
    # that can be unambiguously located.
    for model_name, real_result in real_models.items():

        synthetic_result = None

        possible_keys = [
            model_name,
            model_name.lower(),
            model_name.replace(" ", "_").lower(),
        ]

        for key in possible_keys:
            if key in baseline:
                synthetic_result = baseline[key]
                break

        if synthetic_result is None:
            comparisons[model_name] = {
                "compared": False,
                "reason": (
                    "Matching synthetic model metrics were not found "
                    "in the baseline artifact."
                ),
            }
            continue

        if not isinstance(synthetic_result, dict):
            comparisons[model_name] = {
                "compared": False,
                "reason": "Synthetic model result is not an object.",
            }
            continue

        real_metrics = real_result["metrics"]

        metric_pairs = {}

        for metric_name in [
            "accuracy",
            "macro_f1",
            "weighted_f1",
            "macro_precision",
            "macro_recall",
            "high_recall",
            "critical_recall",
        ]:

            real_value = real_metrics.get(metric_name)

            synthetic_value = synthetic_result.get(metric_name)

            # Support nested metric structure.
            if synthetic_value is None:
                metrics_block = synthetic_result.get("metrics")

                if isinstance(metrics_block, dict):
                    synthetic_value = metrics_block.get(metric_name)

            if isinstance(real_value, (int, float)) and isinstance(
                synthetic_value,
                (int, float),
            ):
                metric_pairs[metric_name] = {
                    "real_data": float(real_value),
                    "synthetic_data": float(synthetic_value),
                    "difference_real_minus_synthetic": float(
                        real_value - synthetic_value
                    ),
                }

        comparisons[model_name] = {
            "compared": bool(metric_pairs),
            "metrics": metric_pairs,
            "reason": (
                None
                if metric_pairs
                else "No matching metrics were available."
            ),
        }

    return {
        "performed": True,
        "baseline": synthetic_baseline,
        "models": comparisons,
    }


# ============================================================================
# LIMITATIONS
# ============================================================================

def build_limitations(
    y_test: np.ndarray,
    model_results: Dict[str, Any],
    synthetic_baseline: Dict[str, Any],
) -> List[str]:

    limitations: List[str] = []

    distribution = class_distribution(y_test)

    if distribution["MEDIUM"] == 0:
        limitations.append(
            "The test split contains no MEDIUM samples; MEDIUM-class "
            "precision/recall/F1 cannot be empirically assessed on the test set."
        )

    if distribution["HIGH"] == 0:
        limitations.append(
            "The test split contains no HIGH samples; HIGH recall cannot "
            "be empirically assessed on the test set."
        )

    if distribution["CRITICAL"] == 0:
        limitations.append(
            "The test split contains no CRITICAL samples; CRITICAL recall "
            "cannot be empirically assessed on the test set."
        )

    if distribution["HIGH"] <= 1:
        limitations.append(
            "HIGH-class test support is extremely small, so HIGH recall "
            "is statistically unstable."
        )

    if distribution["CRITICAL"] <= 5:
        limitations.append(
            "CRITICAL-class test support is very small, so CRITICAL recall "
            "is statistically unstable."
        )

    total = len(y_test)

    if total > 0:
        low_fraction = distribution["LOW"] / total

        if low_fraction >= 0.90:
            limitations.append(
                "The test set is heavily dominated by LOW labels; aggregate "
                "accuracy and weighted metrics can therefore appear strong "
                "without demonstrating reliable detection of rare classes."
            )

    limitations.append(
        "The real-world labels represent observable post-merge defect "
        "evidence strength rather than directly measured production business impact."
    )

    limitations.append(
        "Absence of an observed post-merge signal does not prove that a "
        "change was defect-free."
    )

    limitations.append(
        "The evaluation is based on the frozen 2.0.0 real-data split and "
        "should not be generalized beyond the sampled repositories and "
        "labeling policy without additional validation."
    )

    if not synthetic_baseline.get("available"):
        limitations.append(
            "A synthetic-data baseline comparison could not be completed "
            "because a compatible synthetic evaluation artifact was not found."
        )

    return limitations


# ============================================================================
# MAIN
# ============================================================================

def evaluate() -> None:

    print("=" * 70)
    print("ReleaseGuard — Real-Data Evaluation")
    print("=" * 70)
    print(f"Model version  : {MODEL_VERSION}")
    print(f"Feature version: {FEATURE_VERSION}")

    # ----------------------------------------------------------------------
    # Validate inputs
    # ----------------------------------------------------------------------

    require_file(
        TEST_FILE,
        "real test dataset",
    )

    require_file(
        LOGISTIC_MODEL_FILE,
        "Logistic Regression model",
    )

    require_file(
        XGBOOST_MODEL_FILE,
        "XGBoost model",
    )

    require_file(
        MODEL_METADATA_FILE,
        "model metadata",
    )

    require_file(
        FEATURE_SCHEMA_FILE,
        "feature schema",
    )

    # ----------------------------------------------------------------------
    # Load test data
    # ----------------------------------------------------------------------

    print("\nLoading frozen test dataset...")

    test_records = load_jsonl(TEST_FILE)

    print(f"Test records: {len(test_records)}")

    X_test, y_test = extract_matrix(test_records)

    print(f"Feature count: {X_test.shape[1]}")

    test_distribution = class_distribution(y_test)

    print("\nTest label distribution:")

    for class_name in CLASS_NAMES:
        print(
            f"  {class_name:<9} "
            f"{test_distribution[class_name]}"
        )

    # ----------------------------------------------------------------------
    # Evaluate models
    # ----------------------------------------------------------------------

    logistic_result = evaluate_model(
        "Logistic Regression",
        LOGISTIC_MODEL_FILE,
        X_test,
        y_test,
    )

    xgboost_result = evaluate_model(
        "XGBoost",
        XGBOOST_MODEL_FILE,
        X_test,
        y_test,
    )

    model_results = {
        "logistic_regression": logistic_result,
        "xgboost": xgboost_result,
    }

    # ----------------------------------------------------------------------
    # Synthetic baseline
    # ----------------------------------------------------------------------

    print("\nSearching for synthetic-data baseline...")

    synthetic_baseline = load_synthetic_baseline()

    if synthetic_baseline.get("available"):
        print(
            "Synthetic baseline: FOUND"
        )
        print(
            f"  {synthetic_baseline['path']}"
        )
    else:
        print(
            "Synthetic baseline: NOT FOUND"
        )
        print(
            f"  {synthetic_baseline['reason']}"
        )

    comparison = compare_against_synthetic(
        model_results,
        synthetic_baseline,
    )

    # ----------------------------------------------------------------------
    # Model-level summary
    # ----------------------------------------------------------------------

    model_summary: Dict[str, Any] = {}

    for model_key, result in model_results.items():

        metrics = result["metrics"]

        model_summary[model_key] = {
            "accuracy": metrics["accuracy"],
            "macro_f1": metrics["macro_f1"],
            "weighted_f1": metrics["weighted_f1"],
            "macro_precision": metrics["macro_precision"],
            "macro_recall": metrics["macro_recall"],
            "high_recall": metrics["high_recall"],
            "critical_recall": metrics["critical_recall"],
        }

    # ----------------------------------------------------------------------
    # Limitations
    # ----------------------------------------------------------------------

    limitations = build_limitations(
        y_test,
        model_results,
        synthetic_baseline,
    )

    # ----------------------------------------------------------------------
    # Artifact hashes
    # ----------------------------------------------------------------------

    print("\nCalculating artifact hashes...")

    artifact_hashes = {
        "test_dataset_sha256": sha256_file(TEST_FILE),
        "logistic_regression_sha256": sha256_file(
            LOGISTIC_MODEL_FILE
        ),
        "xgboost_sha256": sha256_file(
            XGBOOST_MODEL_FILE
        ),
        "model_metadata_sha256": sha256_file(
            MODEL_METADATA_FILE
        ),
        "feature_schema_sha256": sha256_file(
            FEATURE_SCHEMA_FILE
        ),
    }

    # ----------------------------------------------------------------------
    # Output report
    # ----------------------------------------------------------------------

    report = {
        "schema_version": "1.0.0",
        "created_at_utc": utc_now(),

        "dataset": {
            "dataset_version": MODEL_VERSION,
            "feature_version": FEATURE_VERSION,
            "split": "test",
            "test_records": int(len(test_records)),
            "feature_count": int(X_test.shape[1]),
            "label_distribution": test_distribution,
            "test_file": str(TEST_FILE),
        },

        "models": model_results,

        "summary": model_summary,

        "synthetic_data_baseline_comparison": comparison,

        "limitations": limitations,

        "artifacts": artifact_hashes,
    }

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            report,
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")

    # ----------------------------------------------------------------------
    # Evaluation manifest
    # ----------------------------------------------------------------------

    manifest = {
        "schema_version": "1.0.0",
        "created_at_utc": utc_now(),

        "dataset_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,

        "evaluation": {
            "split": "test",
            "protocol": (
                "Frozen real-data test split; no fitting or hyperparameter "
                "selection performed during evaluation."
            ),
            "metrics": [
                "accuracy",
                "macro_precision",
                "macro_recall",
                "macro_f1",
                "weighted_f1",
                "high_recall",
                "critical_recall",
                "confusion_matrix",
            ],
            "probability_calibration": [
                "multiclass_brier_score",
                "multiclass_log_loss",
                "mean_predicted_confidence",
                "mean_confidence_correct",
                "mean_confidence_incorrect",
                "mean_true_class_probability",
            ],
        },

        "inputs": {
            "test_dataset": str(TEST_FILE),
            "logistic_regression": str(LOGISTIC_MODEL_FILE),
            "xgboost": str(XGBOOST_MODEL_FILE),
            "model_metadata": str(MODEL_METADATA_FILE),
            "feature_schema": str(FEATURE_SCHEMA_FILE),
        },

        "hashes": artifact_hashes,

        "test_records": int(len(test_records)),
        "feature_count": int(X_test.shape[1]),

        "label_distribution": test_distribution,

        "models_evaluated": [
            "logistic_regression",
            "xgboost",
        ],

        "synthetic_baseline_comparison": {
            "performed": comparison.get("performed", False),
            "baseline_available": synthetic_baseline.get(
                "available",
                False,
            ),
        },

        "limitations_count": len(limitations),
        "limitations": limitations,

        "output": {
            "evaluation": str(OUTPUT_FILE),
            "manifest": str(MANIFEST_FILE),
        },
    }

    with MANIFEST_FILE.open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            manifest,
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")

    # ----------------------------------------------------------------------
    # Final output
    # ----------------------------------------------------------------------

    print("\n" + "=" * 70)
    print("REAL-DATA EVALUATION COMPLETE")
    print("=" * 70)

    print(f"Model version : {MODEL_VERSION}")
    print(f"Feature version: {FEATURE_VERSION}")

    print("\nTest records:")
    print(f"  {len(test_records)}")

    print("\nFeature count:")
    print(f"  {X_test.shape[1]}")

    print("\nLabel distribution:")

    for class_name in CLASS_NAMES:
        count = test_distribution[class_name]

        percentage = (
            count / len(y_test) * 100
            if len(y_test) > 0
            else 0.0
        )

        print(
            f"  {class_name:<9} "
            f"{count:>4} "
            f"({percentage:6.2f}%)"
        )

    print("\nLogistic Regression — Test")

    for key in [
        "accuracy",
        "macro_f1",
        "weighted_f1",
        "macro_precision",
        "macro_recall",
    ]:
        print(
            f"  {key:<17}: "
            f"{logistic_result['metrics'][key]:.4f}"
        )

    print(
        "  HIGH recall       : "
        + (
            f"{logistic_result['metrics']['high_recall']:.4f}"
            if logistic_result["metrics"]["high_recall"] is not None
            else "N/A"
        )
    )

    print(
        "  CRITICAL recall   : "
        + (
            f"{logistic_result['metrics']['critical_recall']:.4f}"
            if logistic_result["metrics"]["critical_recall"] is not None
            else "N/A"
        )
    )

    print("\nXGBoost — Test")

    for key in [
        "accuracy",
        "macro_f1",
        "weighted_f1",
        "macro_precision",
        "macro_recall",
    ]:
        print(
            f"  {key:<17}: "
            f"{xgboost_result['metrics'][key]:.4f}"
        )

    print(
        "  HIGH recall       : "
        + (
            f"{xgboost_result['metrics']['high_recall']:.4f}"
            if xgboost_result["metrics"]["high_recall"] is not None
            else "N/A"
        )
    )

    print(
        "  CRITICAL recall   : "
        + (
            f"{xgboost_result['metrics']['critical_recall']:.4f}"
            if xgboost_result["metrics"]["critical_recall"] is not None
            else "N/A"
        )
    )

    print("\nProbability calibration:")

    for model_key, result in model_results.items():

        calibration = result["probability_calibration"]

        print(
            f"  {model_key}: "
            + (
                "EVALUATED"
                if calibration["applicable"]
                else "NOT AVAILABLE"
            )
        )

    print("\nSynthetic-data baseline:")
    print(
        "  "
        + (
            "COMPARED"
            if comparison.get("performed")
            else "NOT COMPARED"
        )
    )

    print("\nLimitations documented:")
    print(f"  {len(limitations)}")

    print("\nEvaluation:")
    print(f"  {OUTPUT_FILE}")

    print("\nManifest:")
    print(f"  {MANIFEST_FILE}")

    print("=" * 70)


if __name__ == "__main__":
    try:
        evaluate()

    except KeyboardInterrupt:
        print("\nEvaluation interrupted.")
        sys.exit(130)

    except Exception as exc:
        print("\n" + "=" * 70)
        print("REAL-DATA EVALUATION FAILED")
        print("=" * 70)
        print(
            f"{type(exc).__name__}: {exc}"
        )
        sys.exit(1)