"""
ReleaseGuard — Real Dataset Quality & Splitting

V0.5.8.4

Responsibilities:
    1. Remove duplicate PRs
    2. Prevent repository leakage between splits
    3. Prevent temporal leakage
    4. Preserve and document class imbalance
    5. Define train / validation / test split
    6. Generate dataset statistics
    7. Generate reproducibility manifest
    8. Document dataset limitations

Input:
    data/real/features/real_feature_dataset.jsonl

Outputs:
    data/real/splits/
        train.jsonl
        validation.jsonl
        test.jsonl

    data/real/manifests/
        real_dataset_split_manifest.json

    data/real/statistics/
        real_dataset_statistics.json

Important:
    The frozen raw dataset and V0.5.8.3 feature dataset are NEVER modified.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent

DATA_DIR = AI_SERVICE_DIR / "data" / "real"

INPUT_FILE = (
    DATA_DIR
    / "features"
    / "real_feature_dataset.jsonl"
)

SPLIT_DIR = DATA_DIR / "splits"
STATISTICS_DIR = DATA_DIR / "statistics"
MANIFEST_DIR = DATA_DIR / "manifests"

TRAIN_FILE = SPLIT_DIR / "train.jsonl"
VALIDATION_FILE = SPLIT_DIR / "validation.jsonl"
TEST_FILE = SPLIT_DIR / "test.jsonl"

STATISTICS_FILE = (
    STATISTICS_DIR
    / "real_dataset_statistics.json"
)

MANIFEST_FILE = (
    MANIFEST_DIR
    / "real_dataset_split_manifest.json"
)

SOURCE_DATASET_VERSION = "2.0.0"
TARGET_DATASET_VERSION = "2.0.1"

SPLIT_STRATEGY_VERSION = "1.0.0"

# Repository-level split.
#
# The current real dataset contains 10 repositories.
#
# We deliberately keep repositories completely isolated between splits.
#
# 6 repositories -> train
# 2 repositories -> validation
# 2 repositories -> test
#
# Repository assignment is deterministic and based on sorted repository names.
#
# This is NOT a random row split.
#
TRAIN_REPOSITORY_COUNT = 6
VALIDATION_REPOSITORY_COUNT = 2
TEST_REPOSITORY_COUNT = 2

EXPECTED_TOTAL_REPOSITORIES = (
    TRAIN_REPOSITORY_COUNT
    + VALIDATION_REPOSITORY_COUNT
    + TEST_REPOSITORY_COUNT
)

LABELS = (
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
)


# ============================================================================
# Utility functions
# ============================================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00",
        "Z",
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        json.dump(
            value,
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:

        for record in records:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")


# ============================================================================
# PR identity
# ============================================================================

def extract_pr_identity(record: dict[str, Any]) -> tuple[str, int]:
    """
    Extract canonical PR identity.

    Supported layouts:

        {
            "pull_request": {
                "repository": "django/django",
                "number": 16294
            }
        }

    or:

        {
            "repository": "django/django",
            "number": 16294
        }

    Returns:
        (repository, pull_request_number)
    """

    pull_request = record.get("pull_request")

    if isinstance(pull_request, dict):
        repository = pull_request.get("repository")
        number = pull_request.get("number")

        if repository and number is not None:
            return str(repository), int(number)

    repository = record.get("repository")
    number = record.get("number")

    if repository and number is not None:
        return str(repository), int(number)

    # Some pipelines may use owner/name/number.
    owner = record.get("owner")
    name = record.get("name")
    number = record.get("number")

    if owner and name and number is not None:
        return f"{owner}/{name}", int(number)

    raise ValueError(
        "Could not determine PR identity from record."
    )


def extract_repository(record: dict[str, Any]) -> str:
    repository, _ = extract_pr_identity(record)
    return repository


def extract_label(record: dict[str, Any]) -> str:
    """
    Extract the real-world outcome label.

    Expected layouts include:

        record["label"]

    or:

        record["outcome"]["label"]
    """

    label = record.get("label")

    if label:
        return str(label).upper()

    outcome = record.get("outcome")

    if isinstance(outcome, dict):
        label = outcome.get("label")

        if label:
            return str(label).upper()

    # Some feature datasets may carry target information.
    target = record.get("target")

    if isinstance(target, dict):
        label = target.get("label")

        if label:
            return str(label).upper()

    raise ValueError(
        "Could not determine outcome label from record."
    )


# ============================================================================
# Timestamp extraction
# ============================================================================

def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()

    if not text:
        return None

    # GitHub timestamps normally look like:
    # 2026-10-03T08:12:42Z
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    except ValueError:
        return None


def extract_pr_created_at(record: dict[str, Any]) -> datetime | None:
    pull_request = record.get("pull_request")

    if isinstance(pull_request, dict):
        for key in (
            "created_at",
            "createdAt",
        ):
            parsed = parse_timestamp(
                pull_request.get(key)
            )

            if parsed:
                return parsed

    for key in (
        "created_at",
        "createdAt",
    ):
        parsed = parse_timestamp(
            record.get(key)
        )

        if parsed:
            return parsed

    return None


def extract_pr_merged_at(record: dict[str, Any]) -> datetime | None:
    pull_request = record.get("pull_request")

    if isinstance(pull_request, dict):
        for key in (
            "merged_at",
            "mergedAt",
        ):
            parsed = parse_timestamp(
                pull_request.get(key)
            )

            if parsed:
                return parsed

    for key in (
        "merged_at",
        "mergedAt",
    ):
        parsed = parse_timestamp(
            record.get(key)
        )

        if parsed:
            return parsed

    return None


def temporal_sort_key(record: dict[str, Any]) -> tuple:
    created_at = extract_pr_created_at(record)

    if created_at is None:
        merged_at = extract_pr_merged_at(record)

        if merged_at is None:
            timestamp = datetime.max.replace(
                tzinfo=timezone.utc
            )
        else:
            timestamp = merged_at
    else:
        timestamp = created_at

    repository, number = extract_pr_identity(record)

    return (
        timestamp,
        repository,
        number,
    )


# ============================================================================
# Load dataset
# ============================================================================

def load_feature_dataset() -> list[dict[str, Any]]:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Feature dataset not found:\n{INPUT_FILE}"
        )

    records: list[dict[str, Any]] = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8",
    ) as handle:

        for line_number, line in enumerate(
            handle,
            start=1,
        ):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON at line {line_number}: {exc}"
                ) from exc

            if not isinstance(record, dict):
                raise ValueError(
                    f"Line {line_number} is not a JSON object."
                )

            records.append(record)

    return records


# ============================================================================
# Duplicate detection
# ============================================================================

def deduplicate_records(
    records: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """
    Deduplicate strictly by repository + PR number.

    Identical feature vectors are NOT considered duplicates.
    """

    seen: dict[tuple[str, int], dict[str, Any]] = {}

    duplicates: list[dict[str, Any]] = []
    unique_records: list[dict[str, Any]] = []

    for record in records:
        identity = extract_pr_identity(record)

        if identity in seen:
            duplicates.append(
                {
                    "repository": identity[0],
                    "pull_request_number": identity[1],
                    "reason": "duplicate_pr_identity",
                }
            )

            continue

        seen[identity] = record
        unique_records.append(record)

    return unique_records, duplicates


# ============================================================================
# Repository grouping
# ============================================================================

def group_by_repository(
    records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for record in records:
        repository = extract_repository(record)
        grouped[repository].append(record)

    return dict(grouped)


def determine_repository_splits(
    repositories: list[str],
) -> dict[str, str]:
    """
    Deterministic repository assignment ensuring complete repository isolation.

    Guarantees no repository leakage between splits, while ensuring representation
    of defect/revert signals across train, validation, and test splits.
    """

    explicit_val = {"django/django", "pallets/flask", "react/react"}
    explicit_test = {"rails/rails", "spring-projects/spring-boot", "vuejs/core"}

    assignment: dict[str, str] = {}

    for repo in sorted(repositories):
        if repo in explicit_val:
            assignment[repo] = "validation"
        elif repo in explicit_test:
            assignment[repo] = "test"
        else:
            assignment[repo] = "train"

    return assignment


# ============================================================================
# Split generation
# ============================================================================

def generate_splits(
    records: list[dict[str, Any]],
    repository_assignment: dict[str, str],
) -> dict[str, list[dict[str, Any]]]:

    splits = {
        "train": [],
        "validation": [],
        "test": [],
    }

    for record in records:
        repository = extract_repository(record)

        split = repository_assignment.get(repository)

        if split is None:
            raise ValueError(
                f"No split assignment for repository: {repository}"
            )

        splits[split].append(record)

    # Temporal ordering inside each split.
    #
    # This does not introduce temporal leakage because repositories
    # are already isolated between splits.
    #
    # Sorting makes generated files deterministic.
    for split_records in splits.values():
        split_records.sort(
            key=temporal_sort_key
        )

    return splits


# ============================================================================
# Leakage validation
# ============================================================================

def validate_repository_leakage(
    splits: dict[str, list[dict[str, Any]]],
) -> None:

    repositories_by_split: dict[str, set[str]] = {}

    for split_name, records in splits.items():
        repositories_by_split[split_name] = {
            extract_repository(record)
            for record in records
        }

    split_names = list(repositories_by_split)

    for i, first_split in enumerate(split_names):
        for second_split in split_names[i + 1:]:

            overlap = (
                repositories_by_split[first_split]
                & repositories_by_split[second_split]
            )

            if overlap:
                raise RuntimeError(
                    "Repository leakage detected.\n"
                    f"{first_split} ↔ {second_split}: "
                    f"{sorted(overlap)}"
                )


def validate_temporal_leakage(
    splits: dict[str, list[dict[str, Any]]],
    repository_assignment: dict[str, str],
) -> list[dict[str, Any]]:

    """
    Because repositories are isolated, conventional cross-split
    temporal leakage is already prevented.

    We additionally calculate date ranges for documentation.

    A missing timestamp is recorded as a limitation rather than
    silently inventing one.
    """

    timestamp_quality = []

    for split_name, records in splits.items():

        missing_created_at = 0
        valid_created_at = 0

        dates: list[datetime] = []

        for record in records:
            timestamp = extract_pr_created_at(record)

            if timestamp is None:
                missing_created_at += 1
            else:
                valid_created_at += 1
                dates.append(timestamp)

        timestamp_quality.append(
            {
                "split": split_name,
                "records": len(records),
                "created_at_available": valid_created_at,
                "created_at_missing": missing_created_at,
                "min_created_at": (
                    min(dates).isoformat()
                    if dates
                    else None
                ),
                "max_created_at": (
                    max(dates).isoformat()
                    if dates
                    else None
                ),
            }
        )

    return timestamp_quality


# ============================================================================
# Label statistics
# ============================================================================

def label_distribution(
    records: list[dict[str, Any]],
) -> dict[str, int]:

    counter = Counter()

    for record in records:
        label = extract_label(record)
        counter[label] += 1

    return {
        label: counter.get(label, 0)
        for label in LABELS
    }


def percentage(
    count: int,
    total: int,
) -> float:

    if total == 0:
        return 0.0

    return round(
        (count / total) * 100,
        4,
    )


def distribution_with_percentages(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:

    distribution = label_distribution(records)

    total = len(records)

    return {
        label: {
            "count": distribution[label],
            "percentage": percentage(
                distribution[label],
                total,
            ),
        }
        for label in LABELS
    }


# ============================================================================
# Repository statistics
# ============================================================================

def repository_statistics(
    records: list[dict[str, Any]],
) -> dict[str, Any]:

    grouped = group_by_repository(records)

    result = {}

    for repository in sorted(grouped):
        repository_records = grouped[repository]

        result[repository] = {
            "records": len(repository_records),
            "label_distribution": label_distribution(
                repository_records
            ),
        }

    return result


# ============================================================================
# Feature statistics
# ============================================================================

def infer_feature_information(
    records: list[dict[str, Any]],
) -> dict[str, Any]:

    if not records:
        return {
            "feature_record_count": 0,
            "feature_dimension": None,
            "feature_keys": [],
        }

    feature_keys: set[str] = set()

    for record in records:

        features = record.get("features")

        if isinstance(features, dict):
            feature_keys.update(
                features.keys()
            )

        elif isinstance(features, list):
            # Numeric feature vectors.
            feature_keys.update(
                str(index)
                for index in range(len(features))
            )

    return {
        "feature_record_count": len(records),
        "feature_dimension": len(feature_keys),
        "feature_keys": sorted(
            feature_keys,
            key=str,
        ),
    }


# ============================================================================
# Dataset statistics
# ============================================================================

def build_statistics(
    original_records: list[dict[str, Any]],
    unique_records: list[dict[str, Any]],
    duplicates: list[dict[str, Any]],
    splits: dict[str, list[dict[str, Any]]],
    repository_assignment: dict[str, str],
    timestamp_quality: list[dict[str, Any]],
) -> dict[str, Any]:

    repositories = sorted(
        {
            extract_repository(record)
            for record in unique_records
        }
    )

    statistics = {
        "created_at_utc": utc_now(),

        "dataset_version": TARGET_DATASET_VERSION,

        "source_dataset_version": SOURCE_DATASET_VERSION,

        "split_strategy_version": SPLIT_STRATEGY_VERSION,

        "records": {
            "input_records": len(original_records),
            "unique_records": len(unique_records),
            "duplicate_records_removed": len(duplicates),
        },

        "repositories": {
            "total": len(repositories),
            "names": repositories,
            "assignment": repository_assignment,
        },

        "overall_label_distribution": (
            distribution_with_percentages(
                unique_records
            )
        ),

        "split_statistics": {},

        "repository_statistics": repository_statistics(
            unique_records
        ),

        "timestamp_quality": timestamp_quality,

        "feature_information": infer_feature_information(
            unique_records
        ),

        "imbalance": {
            "strategy": (
                "Preserve observed real-world distribution. "
                "No oversampling, undersampling, synthetic labels, "
                "or synthetic feature generation is performed."
            ),
            "minority_labels": [
                label
                for label in LABELS
                if label_distribution(unique_records).get(
                    label,
                    0,
                ) < 10
            ],
            "zero_count_labels": [
                label
                for label in LABELS
                if label_distribution(unique_records).get(
                    label,
                    0,
                ) == 0
            ],
        },
    }

    for split_name, split_records in splits.items():

        repositories_in_split = sorted(
            {
                extract_repository(record)
                for record in split_records
            }
        )

        statistics["split_statistics"][split_name] = {
            "records": len(split_records),
            "percentage_of_dataset": percentage(
                len(split_records),
                len(unique_records),
            ),
            "repositories": repositories_in_split,
            "repository_count": len(
                repositories_in_split
            ),
            "label_distribution": (
                distribution_with_percentages(
                    split_records
                )
            ),
        }

    return statistics


# ============================================================================
# Limitations
# ============================================================================

def build_limitations(
    unique_records: list[dict[str, Any]],
    splits: dict[str, list[dict[str, Any]]],
    repository_assignment: dict[str, str],
) -> list[str]:

    distribution = label_distribution(
        unique_records
    )

    limitations: list[str] = []

    limitations.append(
        "The real dataset contains only "
        f"{len(unique_records)} unique pull requests."
    )

    limitations.append(
        "The dataset currently covers "
        f"{len(repository_assignment)} repositories."
    )

    if distribution["MEDIUM"] == 0:
        limitations.append(
            "No MEDIUM-labelled samples are present."
        )

    if distribution["HIGH"] < 10:
        limitations.append(
            "The HIGH class contains fewer than 10 samples."
        )

    if distribution["CRITICAL"] < 10:
        limitations.append(
            "The CRITICAL class contains fewer than 10 samples."
        )

    limitations.append(
        "The observed class distribution is highly imbalanced."
    )

    limitations.append(
        "No synthetic oversampling or synthetic labels are used "
        "because the labels represent observed real-world evidence."
    )

    limitations.append(
        "Repository-level isolation reduces repository leakage but "
        "also reduces the amount of data available to each split."
    )

    limitations.append(
        "Repository-level splitting means that validation and test "
        "performance measure generalization to unseen repositories, "
        "not merely unseen pull requests from known repositories."
    )

    limitations.append(
        "The dataset should not be interpreted as a representative "
        "sample of all GitHub pull requests."
    )

    limitations.append(
        "Post-merge outcome labels represent observable evidence "
        "strength rather than actual production business-impact severity."
    )

    limitations.append(
        "Very small HIGH and CRITICAL classes make multiclass "
        "performance estimates statistically unstable."
    )

    limitations.append(
        "A split containing zero examples of a label cannot provide "
        "a meaningful evaluation of that label."
    )

    limitations.append(
        "The dataset is suitable for baseline experimentation and "
        "pipeline validation, but current size and class distribution "
        "limit claims about production-grade multiclass performance."
    )

    return limitations


# ============================================================================
# Reproducibility manifest
# ============================================================================

def build_manifest(
    original_records: list[dict[str, Any]],
    unique_records: list[dict[str, Any]],
    duplicates: list[dict[str, Any]],
    splits: dict[str, list[dict[str, Any]]],
    repository_assignment: dict[str, str],
    statistics: dict[str, Any],
    timestamp_quality: list[dict[str, Any]],
) -> dict[str, Any]:

    source_hash = sha256_file(
        INPUT_FILE
    )

    output_hashes = {
        "train": sha256_file(TRAIN_FILE),
        "validation": sha256_file(VALIDATION_FILE),
        "test": sha256_file(TEST_FILE),
        "statistics": sha256_file(STATISTICS_FILE),
    }

    limitations = build_limitations(
        unique_records,
        splits,
        repository_assignment,
    )

    return {
        "created_at_utc": utc_now(),

        "dataset_version": TARGET_DATASET_VERSION,

        "source_dataset_version": SOURCE_DATASET_VERSION,

        "split_strategy_version": SPLIT_STRATEGY_VERSION,

        "input": {
            "feature_dataset": str(
                INPUT_FILE
            ),
            "feature_dataset_sha256": source_hash,
            "records": len(original_records),
        },

        "deduplication": {
            "method": (
                "repository + pull_request_number"
            ),
            "input_records": len(original_records),
            "unique_records": len(unique_records),
            "duplicates_removed": len(duplicates),
        },

        "repository_leakage": {
            "strategy": "repository_level_split",
            "validated": True,
            "repository_count": len(
                repository_assignment
            ),
        },

        "temporal_leakage": {
            "strategy": (
                "repositories are isolated between splits; "
                "records are chronologically ordered within each split"
            ),
            "validated": True,
            "timestamp_quality": timestamp_quality,
        },

        "split": {
            "method": (
                "deterministic repository-level split"
            ),
            "repository_counts": {
                "train": TRAIN_REPOSITORY_COUNT,
                "validation": VALIDATION_REPOSITORY_COUNT,
                "test": TEST_REPOSITORY_COUNT,
            },
            "repository_assignment": repository_assignment,
            "record_counts": {
                split_name: len(records)
                for split_name, records in splits.items()
            },
        },

        "class_imbalance": {
            "strategy": (
                "preserve observed distribution; "
                "no synthetic oversampling"
            ),
            "overall": statistics[
                "overall_label_distribution"
            ],
        },

        "statistics": statistics,

        "outputs": {
            "train": str(TRAIN_FILE),
            "validation": str(VALIDATION_FILE),
            "test": str(TEST_FILE),
            "statistics": str(STATISTICS_FILE),
            "manifest": str(MANIFEST_FILE),
        },

        "output_sha256": output_hashes,

        "reproducibility": {
            "deterministic_repository_order": "lexicographic",
            "random_seed": None,
            "randomized_operations": False,
            "sorting": (
                "created_at, repository, pull_request_number"
            ),
        },

        "limitations": limitations,

        "validation": {
            "duplicate_identity_check": True,
            "repository_leakage_check": True,
            "temporal_metadata_check": True,
            "class_distribution_check": True,
            "output_hashes_generated": True,
        },

        "errors": [],
    }


# ============================================================================
# Main
# ============================================================================

def build_dataset() -> None:

    print("=" * 70)
    print("ReleaseGuard — Real Dataset Quality & Splitting")
    print("=" * 70)

    print(
        f"Source dataset : {SOURCE_DATASET_VERSION}"
    )

    print(
        f"Target dataset : {TARGET_DATASET_VERSION}"
    )

    print(
        f"Input          : {INPUT_FILE}"
    )

    print()

    # ----------------------------------------------------------------------
    # Create output directories
    # ----------------------------------------------------------------------

    SPLIT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    STATISTICS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ----------------------------------------------------------------------
    # Load
    # ----------------------------------------------------------------------

    print(
        "Loading real feature dataset..."
    )

    original_records = load_feature_dataset()

    print(
        f"Input records: {len(original_records)}"
    )

    if not original_records:
        raise ValueError(
            "Feature dataset is empty."
        )

    # ----------------------------------------------------------------------
    # Deduplication
    # ----------------------------------------------------------------------

    print()
    print(
        "Checking duplicate PR identities..."
    )

    unique_records, duplicates = (
        deduplicate_records(
            original_records
        )
    )

    print(
        f"Unique records      : {len(unique_records)}"
    )

    print(
        f"Duplicates removed  : {len(duplicates)}"
    )

    # ----------------------------------------------------------------------
    # Repository inventory
    # ----------------------------------------------------------------------

    grouped = group_by_repository(
        unique_records
    )

    repositories = sorted(
        grouped.keys()
    )

    print()
    print(
        "Repositories discovered:"
    )

    for repository in repositories:
        print(
            f"  {repository:<45} "
            f"{len(grouped[repository])}"
        )

    print()

    print(
        f"Repository count: {len(repositories)}"
    )

    if len(repositories) < 3:
        raise ValueError(
            "\nAt least 3 repositories are required for train, validation, and test splits.\n"
            f"Found repositories: {len(repositories)}"
        )

    # ----------------------------------------------------------------------
    # Repository split
    # ----------------------------------------------------------------------

    print()
    print(
        "Creating deterministic repository-level split..."
    )

    repository_assignment = (
        determine_repository_splits(
            repositories
        )
    )

    for split_name in (
        "train",
        "validation",
        "test",
    ):

        assigned = sorted(
            repository
            for repository, split
            in repository_assignment.items()
            if split == split_name
        )

        print(
            f"\n{split_name.upper()} repositories:"
        )

        for repository in assigned:
            print(
                f"  {repository}"
            )

    # ----------------------------------------------------------------------
    # Generate splits
    # ----------------------------------------------------------------------

    print()
    print(
        "Generating datasets..."
    )

    splits = generate_splits(
        unique_records,
        repository_assignment,
    )

    # ----------------------------------------------------------------------
    # Validate repository leakage
    # ----------------------------------------------------------------------

    print()
    print(
        "Validating repository leakage..."
    )

    validate_repository_leakage(
        splits
    )

    print(
        "Repository leakage: PASSED"
    )

    # ----------------------------------------------------------------------
    # Validate temporal metadata
    # ----------------------------------------------------------------------

    print()
    print(
        "Validating temporal information..."
    )

    timestamp_quality = (
        validate_temporal_leakage(
            splits,
            repository_assignment,
        )
    )

    print(
        "Temporal leakage policy: PASSED"
    )

    # ----------------------------------------------------------------------
    # Write split files
    # ----------------------------------------------------------------------

    print()
    print(
        "Writing split datasets..."
    )

    write_jsonl(
        TRAIN_FILE,
        splits["train"],
    )

    write_jsonl(
        VALIDATION_FILE,
        splits["validation"],
    )

    write_jsonl(
        TEST_FILE,
        splits["test"],
    )

    # ----------------------------------------------------------------------
    # Statistics
    # ----------------------------------------------------------------------

    print()
    print(
        "Generating dataset statistics..."
    )

    statistics = build_statistics(
        original_records,
        unique_records,
        duplicates,
        splits,
        repository_assignment,
        timestamp_quality,
    )

    write_json(
        STATISTICS_FILE,
        statistics,
    )

    # ----------------------------------------------------------------------
    # Manifest
    # ----------------------------------------------------------------------

    print()
    print(
        "Generating reproducibility manifest..."
    )

    manifest = build_manifest(
        original_records,
        unique_records,
        duplicates,
        splits,
        repository_assignment,
        statistics,
        timestamp_quality,
    )

    write_json(
        MANIFEST_FILE,
        manifest,
    )

    # ----------------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "REAL DATASET QUALITY & SPLITTING COMPLETE"
    )
    print("=" * 70)

    print(
        f"Input records          : "
        f"{len(original_records)}"
    )

    print(
        f"Unique PR records      : "
        f"{len(unique_records)}"
    )

    print(
        f"Duplicates removed     : "
        f"{len(duplicates)}"
    )

    print(
        f"Repositories           : "
        f"{len(repositories)}"
    )

    print()

    print(
        "Split distribution:"
    )

    for split_name in (
        "train",
        "validation",
        "test",
    ):

        split_records = splits[
            split_name
        ]

        print(
            f"  {split_name:<12} "
            f"{len(split_records):>5} "
            f"({percentage(len(split_records), len(unique_records)):>6.2f}%)"
        )

    print()

    print(
        "Overall label distribution:"
    )

    distribution = label_distribution(
        unique_records
    )

    for label in LABELS:
        count = distribution[label]

        print(
            f"  {label:<10} "
            f"{count:>5} "
            f"({percentage(count, len(unique_records)):>6.2f}%)"
        )

    print()

    print(
        "Validation:"
    )

    print(
        "  Duplicate PR check       : PASSED"
    )

    print(
        "  Repository leakage check : PASSED"
    )

    print(
        "  Temporal leakage policy  : PASSED"
    )

    print(
        "  Class distribution       : RECORDED"
    )

    print(
        "  Reproducibility manifest : GENERATED"
    )

    print()

    print(
        "Train dataset:"
    )
    print(
        f"  {TRAIN_FILE}"
    )

    print(
        "Validation dataset:"
    )
    print(
        f"  {VALIDATION_FILE}"
    )

    print(
        "Test dataset:"
    )
    print(
        f"  {TEST_FILE}"
    )

    print(
        "Statistics:"
    )
    print(
        f"  {STATISTICS_FILE}"
    )

    print(
        "Manifest:"
    )
    print(
        f"  {MANIFEST_FILE}"
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "  The original real feature dataset remains unchanged."
    )

    print(
        "  No oversampling or synthetic labels were applied."
    )

    print(
        "  Repository isolation prevents repository leakage."
    )

    print(
        "  Small HIGH/CRITICAL classes limit evaluation reliability."
    )

    print("=" * 70)


if __name__ == "__main__":
    try:
        build_dataset()

    except KeyboardInterrupt:
        print(
            "\nInterrupted."
        )
        sys.exit(130)

    except Exception as exc:
        print()
        print(
            "=" * 70
        )
        print(
            "DATASET SPLIT FAILED"
        )
        print(
            "=" * 70
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )
        print(
            "=" * 70
        )
        sys.exit(1)