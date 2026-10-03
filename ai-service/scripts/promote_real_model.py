import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


import os
SERVICE_ROOT = Path(__file__).resolve().parents[1]

MODEL_VERSION = os.getenv("MODEL_VERSION", "2.0.0")
FEATURE_VERSION = "1.0.0"
DATASET_VERSION = "2.0.0"

SOURCE_MODEL = (
    SERVICE_ROOT
    / "data"
    / "real"
    / "models"
    / MODEL_VERSION
    / "xgboost.joblib"
)

SOURCE_METADATA = (
    SERVICE_ROOT
    / "data"
    / "real"
    / "models"
    / MODEL_VERSION
    / "model_metadata.json"
)

PRODUCTION_DIRECTORY = (
    SERVICE_ROOT
    / "artifacts"
    / "models"
    / "xgboost"
    / MODEL_VERSION
)

PRODUCTION_MODEL = PRODUCTION_DIRECTORY / "model.joblib"
PRODUCTION_METADATA = PRODUCTION_DIRECTORY / "metadata.json"

MANIFEST_DIRECTORY = (
    SERVICE_ROOT
    / "data"
    / "real"
    / "manifests"
)

PROMOTION_MANIFEST = (
    MANIFEST_DIRECTORY
    / "production_model_promotion_manifest.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def load_training_metadata() -> dict:
    if not SOURCE_METADATA.exists():
        raise FileNotFoundError(
            f"Training metadata not found:\n"
            f"  {SOURCE_METADATA}"
        )

    metadata = json.loads(
        SOURCE_METADATA.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(metadata, dict):
        raise ValueError(
            "Training metadata must be a JSON object."
        )

    return metadata


def validate_training_metadata(metadata: dict) -> None:
    required = {
        "model_version",
        "feature_version",
        "dataset_version",
    }

    missing = sorted(
        key
        for key in required
        if key not in metadata
    )

    if missing:
        raise ValueError(
            "Training metadata is missing required fields: "
            + ", ".join(missing)
        )

    if str(metadata["model_version"]) != MODEL_VERSION:
        raise ValueError(
            "Training model version mismatch: "
            f"{metadata['model_version']} != "
            f"{MODEL_VERSION}"
        )

    if str(metadata["feature_version"]) != FEATURE_VERSION:
        raise ValueError(
            "Training feature version mismatch: "
            f"{metadata['feature_version']} != "
            f"{FEATURE_VERSION}"
        )

    if str(metadata["dataset_version"]) != DATASET_VERSION:
        raise ValueError(
            "Training dataset version mismatch: "
            f"{metadata['dataset_version']} != "
            f"{DATASET_VERSION}"
        )


def build_production_metadata(
    training_metadata: dict,
    model_sha256: str,
) -> dict:
    return {
        "model_name": "xgboost",
        "model_type": "multiclass_xgboost",
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "dataset_version": DATASET_VERSION,
        "source": "real-data-training",
        "source_model": str(SOURCE_MODEL),
        "source_metadata": str(SOURCE_METADATA),
        "production_artifact": str(PRODUCTION_MODEL),
        "model_sha256": model_sha256,
        "promoted_at_utc": datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "training_metadata": training_metadata,
    }


def build_manifest(
    metadata: dict,
    model_sha256: str,
    metadata_sha256: str,
) -> dict:
    return {
        "schema_version": "1.0.0",
        "operation": "production_model_promotion",
        "status": "SUCCESS",
        "model_name": "xgboost",
        "model_version": MODEL_VERSION,
        "feature_version": FEATURE_VERSION,
        "dataset_version": DATASET_VERSION,
        "source": {
            "model": str(SOURCE_MODEL),
            "metadata": str(SOURCE_METADATA),
        },
        "production": {
            "directory": str(PRODUCTION_DIRECTORY),
            "model": str(PRODUCTION_MODEL),
            "metadata": str(PRODUCTION_METADATA),
        },
        "hashes": {
            "model_sha256": model_sha256,
            "metadata_sha256": metadata_sha256,
        },
        "created_at_utc": datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def promote_model() -> None:
    print("=" * 70)
    print("ReleaseGuard — Production Model Promotion")
    print("=" * 70)

    print(f"Model version  : {MODEL_VERSION}")
    print(f"Feature version: {FEATURE_VERSION}")
    print(f"Dataset version: {DATASET_VERSION}")
    print()

    print("Source model:")
    print(f"  {SOURCE_MODEL}")

    print("Source metadata:")
    print(f"  {SOURCE_METADATA}")

    if not SOURCE_MODEL.exists():
        raise FileNotFoundError(
            f"Source model does not exist:\n"
            f"{SOURCE_MODEL}"
        )

    if not SOURCE_METADATA.exists():
        raise FileNotFoundError(
            f"Source metadata does not exist:\n"
            f"{SOURCE_METADATA}"
        )

    print()
    print("Loading training metadata...")

    training_metadata = load_training_metadata()

    validate_training_metadata(
        training_metadata
    )

    print("Training metadata validation: PASSED")

    print()
    print("Creating production directory...")

    PRODUCTION_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"  {PRODUCTION_DIRECTORY}"
    )

    print()
    print("Copying model artifact...")

    shutil.copy2(
        SOURCE_MODEL,
        PRODUCTION_MODEL,
    )

    print(
        f"  {PRODUCTION_MODEL}"
    )

    model_sha256 = sha256_file(
        PRODUCTION_MODEL
    )

    print()
    print("Model SHA-256:")
    print(f"  {model_sha256}")

    print()
    print("Creating production metadata...")

    production_metadata = build_production_metadata(
        training_metadata,
        model_sha256,
    )

    PRODUCTION_METADATA.write_text(
        json.dumps(
            production_metadata,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    metadata_sha256 = sha256_file(
        PRODUCTION_METADATA
    )

    print(
        f"  {PRODUCTION_METADATA}"
    )

    print()
    print("Verifying production artifacts...")

    if not PRODUCTION_MODEL.exists():
        raise RuntimeError(
            "Production model was not created."
        )

    if not PRODUCTION_METADATA.exists():
        raise RuntimeError(
            "Production metadata was not created."
        )

    verified_model_hash = sha256_file(
        PRODUCTION_MODEL
    )

    if verified_model_hash != model_sha256:
        raise RuntimeError(
            "Production model SHA-256 verification failed."
        )

    loaded_metadata = json.loads(
        PRODUCTION_METADATA.read_text(
            encoding="utf-8"
        )
    )

    if (
        str(loaded_metadata["model_version"])
        != MODEL_VERSION
    ):
        raise RuntimeError(
            "Production model version verification failed."
        )

    if (
        str(loaded_metadata["feature_version"])
        != FEATURE_VERSION
    ):
        raise RuntimeError(
            "Production feature version verification failed."
        )

    if (
        str(loaded_metadata["dataset_version"])
        != DATASET_VERSION
    ):
        raise RuntimeError(
            "Production dataset version verification failed."
        )

    print("  Model artifact: PASSED")
    print("  Metadata: PASSED")
    print("  SHA-256: PASSED")
    print("  Version metadata: PASSED")

    print()
    print("Writing promotion manifest...")

    MANIFEST_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = build_manifest(
        production_metadata,
        model_sha256,
        metadata_sha256,
    )

    PROMOTION_MANIFEST.write_text(
        json.dumps(
            manifest,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        f"  {PROMOTION_MANIFEST}"
    )

    print()
    print("=" * 70)
    print("PRODUCTION MODEL PROMOTION COMPLETE")
    print("=" * 70)

    print(f"Model version  : {MODEL_VERSION}")
    print(f"Feature version: {FEATURE_VERSION}")
    print(f"Dataset version: {DATASET_VERSION}")
    print()

    print("Production model:")
    print(f"  {PRODUCTION_MODEL}")

    print("Production metadata:")
    print(f"  {PRODUCTION_METADATA}")

    print("Promotion manifest:")
    print(f"  {PROMOTION_MANIFEST}")

    print()
    print("Model SHA-256:")
    print(f"  {model_sha256}")

    print("=" * 70)


if __name__ == "__main__":
    try:
        promote_model()
    except Exception as exc:
        print()
        print("=" * 70)
        print("PRODUCTION MODEL PROMOTION FAILED")
        print("=" * 70)
        print(str(exc))
        raise