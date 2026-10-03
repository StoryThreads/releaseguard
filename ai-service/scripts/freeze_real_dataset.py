from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# Paths
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent

DATA_DIR = AI_SERVICE_DIR / "data" / "real"
RAW_DIR = DATA_DIR / "raw"
MANIFESTS_DIR = DATA_DIR / "manifests"

OUTPUT_FILE = MANIFESTS_DIR / "dataset_freeze_manifest.json"

DATASET_VERSION = "1.0.0-real"
FREEZE_SCHEMA_VERSION = "1.0.0"


# ============================================================
# Configuration
# ============================================================

EXCLUDED_DIRECTORIES = {
    "__pycache__",
}

# These are temporary/cache artifacts that are still part of the
# collection provenance but are not included in the frozen dataset
# content hash set unless explicitly present as raw dataset files.
#
# Keep _api_cache included because post-merge signal collection
# depends on the timeline cache for reproducibility.
INCLUDE_ALL_RAW_FILES = True


COLLECTION_MANIFESTS = [
    "repositories.json",
    "pr_collection_manifest.json",
    "pr_files_collection_manifest.json",
    "linked_issue_collection_manifest.json",
    "post_merge_defect_signal_manifest.json",
]


# ============================================================
# Utility functions
# ============================================================

def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """
    Calculate SHA-256 without loading the entire file into memory.
    """
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def relative_path(path: Path) -> str:
    """
    Store paths relative to data/real using POSIX separators so the
    manifest remains portable across operating systems.
    """
    return path.relative_to(DATA_DIR).as_posix()


def collect_raw_files() -> list[Path]:
    """
    Recursively collect all files under data/real/raw.
    """
    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Raw dataset directory not found: {RAW_DIR}"
        )

    files: list[Path] = []

    for path in RAW_DIR.rglob("*"):
        if not path.is_file():
            continue

        if any(
            part in EXCLUDED_DIRECTORIES
            for part in path.parts
        ):
            continue

        files.append(path)

    files.sort(
        key=lambda p: relative_path(p)
    )

    return files


def load_json(path: Path) -> Any:
    with path.open(
        "r",
        encoding="utf-8-sig",
    ) as file:
        return json.load(file)


def collect_manifest_metadata() -> dict[str, Any]:
    """
    Load the existing collection manifests and record their
    SHA-256 hashes. The contents themselves are not duplicated
    into the freeze manifest.
    """
    result: dict[str, Any] = {}

    for filename in COLLECTION_MANIFESTS:
        path = MANIFESTS_DIR / filename

        if not path.exists():
            result[filename] = {
                "exists": False,
                "path": relative_path(path),
            }
            continue

        try:
            parsed = load_json(path)

            result[filename] = {
                "exists": True,
                "path": relative_path(path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "json_valid": True,
                "top_level_keys": (
                    sorted(parsed.keys())
                    if isinstance(parsed, dict)
                    else None
                ),
            }

        except Exception as exc:
            result[filename] = {
                "exists": True,
                "path": relative_path(path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "json_valid": False,
                "error": str(exc),
            }

    return result


def build_file_records(
    files: list[Path],
) -> tuple[list[dict[str, Any]], int]:
    """
    Hash every raw dataset file and return deterministic records.
    """
    records: list[dict[str, Any]] = []
    total_bytes = 0

    total = len(files)

    for index, path in enumerate(files, start=1):
        size = path.stat().st_size
        digest = sha256_file(path)

        record = {
            "path": relative_path(path),
            "size_bytes": size,
            "sha256": digest,
        }

        records.append(record)
        total_bytes += size

        if index == 1 or index % 100 == 0 or index == total:
            print(
                f"[{index}/{total}] Hashed "
                f"{relative_path(path)}"
            )

    return records, total_bytes


def build_dataset_digest(
    file_records: list[dict[str, Any]],
) -> str:
    """
    Build a deterministic dataset-level SHA-256 digest.

    The digest is calculated from:

        relative path
        file SHA-256

    for every file, in sorted order.

    Therefore changing even one file or its path changes the
    dataset digest.
    """
    digest = hashlib.sha256()

    for record in file_records:
        line = (
            f"{record['path']}\t"
            f"{record['sha256']}\n"
        )

        digest.update(
            line.encode("utf-8")
        )

    return digest.hexdigest()


def validate_required_manifests(
    manifest_metadata: dict[str, Any],
) -> list[str]:
    missing: list[str] = []

    for filename, metadata in manifest_metadata.items():
        if not metadata.get("exists"):
            missing.append(filename)

    return missing


# ============================================================
# Main
# ============================================================

def main() -> int:
    print("=" * 70)
    print("ReleaseGuard — Real Dataset Freeze")
    print("=" * 70)

    print(f"Dataset version : {DATASET_VERSION}")
    print(f"Raw directory   : {RAW_DIR}")
    print(f"Freeze manifest : {OUTPUT_FILE}")
    print()

    # --------------------------------------------------------
    # Validate directories
    # --------------------------------------------------------

    if not DATA_DIR.exists():
        print(
            f"ERROR: Dataset directory does not exist:\n"
            f"{DATA_DIR}"
        )
        return 1

    if not RAW_DIR.exists():
        print(
            f"ERROR: Raw dataset directory does not exist:\n"
            f"{RAW_DIR}"
        )
        return 1

    MANIFESTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Collect files
    # --------------------------------------------------------

    print("Discovering raw dataset files...")

    raw_files = collect_raw_files()

    if not raw_files:
        print(
            "ERROR: No raw dataset files were found."
        )
        return 1

    print(
        f"Raw files discovered: {len(raw_files)}"
    )
    print()

    # --------------------------------------------------------
    # Hash raw dataset
    # --------------------------------------------------------

    print("Calculating SHA-256 hashes...")
    print()

    file_records, total_bytes = build_file_records(
        raw_files
    )

    dataset_digest = build_dataset_digest(
        file_records
    )

    print()
    print(
        f"Total files : {len(file_records)}"
    )
    print(
        f"Total bytes : {total_bytes:,}"
    )
    print(
        f"Dataset SHA : {dataset_digest}"
    )
    print()

    # --------------------------------------------------------
    # Collection manifests
    # --------------------------------------------------------

    print("Checking collection manifests...")

    manifest_metadata = collect_manifest_metadata()

    missing_manifests = validate_required_manifests(
        manifest_metadata
    )

    for filename, metadata in manifest_metadata.items():
        status = (
            "OK"
            if metadata.get("exists")
            and metadata.get("json_valid", False)
            else "MISSING/INVALID"
        )

        print(
            f"  {filename}: {status}"
        )

    print()

    if missing_manifests:
        print(
            "WARNING: Required collection manifests are missing:"
        )

        for filename in missing_manifests:
            print(
                f"  - {filename}"
            )

        print()
        print(
            "The raw dataset will still be hashed, "
            "but the freeze manifest will record these "
            "missing manifests."
        )

    # --------------------------------------------------------
    # Build freeze manifest
    # --------------------------------------------------------

    freeze_timestamp = utc_now()

    freeze_manifest: dict[str, Any] = {
        "schema_version": FREEZE_SCHEMA_VERSION,
        "dataset_type": "releaseguard-real-world",
        "dataset_version": DATASET_VERSION,

        "freeze": {
            "frozen_at": freeze_timestamp,
            "status": "FROZEN",
            "immutability_policy": (
                "Raw dataset files under data/real/raw/ "
                "must not be modified after freeze. "
                "Any change requires creation of a new "
                "dataset version."
            ),
        },

        "source": {
            "type": "public_github_repositories",
            "collection_method": "GitHub REST API",
            "private_repositories_collected": False,
        },

        "dataset": {
            "raw_directory": "raw",
            "file_count": len(file_records),
            "total_size_bytes": total_bytes,
            "sha256": dataset_digest,
        },

        "integrity": {
            "algorithm": "SHA-256",
            "hash_scope": (
                "Every file recursively contained under "
                "data/real/raw/"
            ),
            "path_encoding": "UTF-8 POSIX-style relative paths",
            "deterministic": True,
        },

        "collection_manifests": manifest_metadata,

        "files": file_records,
    }

    # --------------------------------------------------------
    # Write freeze manifest
    # --------------------------------------------------------

    temporary_file = OUTPUT_FILE.with_suffix(
        ".json.tmp"
    )

    with temporary_file.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        json.dump(
            freeze_manifest,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    temporary_file.replace(
        OUTPUT_FILE
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print("=" * 70)
    print("DATASET FREEZE COMPLETE")
    print("=" * 70)

    print(
        f"Dataset version : {DATASET_VERSION}"
    )

    print(
        f"Files frozen    : {len(file_records)}"
    )

    print(
        f"Total size      : {total_bytes:,} bytes"
    )

    print(
        f"Dataset SHA-256 : {dataset_digest}"
    )

    print()
    print(
        "Freeze manifest:"
    )
    print(
        f"  {OUTPUT_FILE}"
    )

    print()
    print(
        "IMPORTANT:"
    )
    print(
        "  Treat data/real/raw/ as immutable."
    )
    print(
        "  Any future modification requires a new "
        "dataset version."
    )

    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())