from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import requests


# ============================================================
# PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = AI_SERVICE_DIR.parent

DATA_DIR = AI_SERVICE_DIR / "data" / "real"

RAW_PR_DIR = DATA_DIR / "raw" / "pull_requests"
LABEL_FILE = DATA_DIR / "labeled" / "real_outcome_labels.jsonl"
SIGNAL_DIR = DATA_DIR / "raw" / "post_merge_defect_signals"

FEATURE_DIR = DATA_DIR / "features"
MANIFEST_DIR = DATA_DIR / "manifests"

SNAPSHOT_FILE = (
    FEATURE_DIR / "real_change_snapshots.jsonl"
)

FEATURE_FILE = (
    FEATURE_DIR / "real_feature_dataset.jsonl"
)

MANIFEST_FILE = (
    MANIFEST_DIR / "real_feature_dataset_manifest.json"
)


# ============================================================
# DATASET VERSIONS
# ============================================================

SOURCE_DATASET_VERSION = "1.0.0-real"
TARGET_DATASET_VERSION = "2.0.0"

FEATURE_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"


# ============================================================
# BACKEND
# ============================================================

BACKEND_URL = os.getenv(
    "RELEASEGUARD_BACKEND_URL",
    "http://localhost:8080",
).rstrip("/")

ANALYSIS_ENDPOINT = os.getenv(
    "RELEASEGUARD_ANALYSIS_ENDPOINT",
    f"{BACKEND_URL}/api/analysis/snapshot",
)

HTTP_TIMEOUT_SECONDS = int(
    os.getenv(
        "RELEASEGUARD_ANALYSIS_TIMEOUT",
        "120",
    )
)

REQUEST_DELAY_SECONDS = float(
    os.getenv(
        "RELEASEGUARD_ANALYSIS_DELAY",
        "0.10",
    )
)

MAX_RETRIES = 3


# ============================================================
# REQUIRED FEATURE KEYS
#
# The current ReleaseGuard feature pipeline is expected to
# produce the feature vector used by the ML service.
#
# We deliberately do NOT fabricate missing features.
# ============================================================

EXPECTED_MIN_FEATURE_COUNT = 1


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path: Path) -> Any:
    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        return json.load(handle)


def read_jsonl(
    path: Path,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    with path.open(
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
                    f"Invalid JSONL at "
                    f"{path}:{line_number}: {exc}"
                ) from exc

            if not isinstance(record, dict):
                raise ValueError(
                    f"Expected JSON object at "
                    f"{path}:{line_number}"
                )

            records.append(record)

    return records


def write_jsonl(
    path: Path,
    records: list[dict[str, Any]],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:

        for record in records:
            handle.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(
                        ",",
                        ":",
                    ),
                )
            )

            handle.write("\n")

    temporary.replace(path)


def write_json(
    path: Path,
    data: Any,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:

        json.dump(
            data,
            handle,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )

        handle.write("\n")

    temporary.replace(path)


# ============================================================
# HASHING
# ============================================================

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def sha256_jsonl(
    records: list[dict[str, Any]],
) -> str:

    digest = hashlib.sha256()

    for record in records:
        encoded = (
            json.dumps(
                record,
                ensure_ascii=False,
                sort_keys=True,
                separators=(
                    ",",
                    ":",
                ),
            )
            + "\n"
        ).encode("utf-8")

        digest.update(encoded)

    return digest.hexdigest()


# ============================================================
# PR IDENTITY
# ============================================================

def extract_pr_identity(
    payload: dict[str, Any],
) -> tuple[str, str, int] | None:

    pull_request = payload.get("pull_request")
    if not isinstance(pull_request, dict):
        pull_request = {}

    repo_raw = (
        payload.get("repository")
        or pull_request.get("repository")
    )

    owner = payload.get("owner") or pull_request.get("owner")
    repository = None

    if isinstance(repo_raw, dict):
        repository = repo_raw.get("full_name") or repo_raw.get("name")
        raw_owner = repo_raw.get("owner")
        if isinstance(raw_owner, dict):
            owner = owner or raw_owner.get("login")
        elif isinstance(raw_owner, str):
            owner = owner or raw_owner
    elif isinstance(repo_raw, str):
        repository = repo_raw

    if not owner and repository and "/" in repository:
        parts = repository.split("/", 1)
        owner = parts[0]

    number = (
        payload.get("number")
        or payload.get("pull_request_number")
        or pull_request.get("number")
        or pull_request.get("pull_request_number")
    )

    if not owner or not repository or number is None:
        return None

    try:
        number = int(number)
    except (
        TypeError,
        ValueError,
    ):
        return None

    return (
        str(owner),
        str(repository),
        number,
    )


# ============================================================
# PR DISCOVERY
# ============================================================

def discover_pr_files() -> list[Path]:

    if not RAW_PR_DIR.exists():
        raise FileNotFoundError(
            "Raw PR directory does not exist: "
            f"{RAW_PR_DIR}"
        )

    files = sorted(
        RAW_PR_DIR.rglob(
            "pr-*.json"
        )
    )

    if not files:
        raise RuntimeError(
            "No raw PR records found."
        )

    return files


# ============================================================
# CHANGE SNAPSHOT
# ============================================================

def build_change_snapshot(
    pr_record: dict[str, Any],
) -> dict[str, Any]:

    identity = extract_pr_identity(
        pr_record
    )

    if identity is None:
        raise ValueError(
            "Could not determine PR identity."
        )

    owner, repository, number = identity

    pull_request = pr_record.get(
        "pull_request",
        pr_record,
    )

    if not isinstance(
        pull_request,
        dict,
    ):
        raise ValueError(
            "pull_request must be an object."
        )

    head = pull_request.get(
        "head",
        {},
    )

    base = pull_request.get(
        "base",
        {},
    )

    if not isinstance(head, dict):
        head = {}

    if not isinstance(base, dict):
        base = {}

    # --------------------------------------------------------
    # Locate changed files.
    #
    # The real dataset has used more than one raw shape over
    # the collection stages, so support the already-existing
    # forms without inventing new data.
    # --------------------------------------------------------

    raw_files = (
        pr_record.get(
            "files"
        )
        or pr_record.get(
            "changedFiles"
        )
        or pr_record.get(
            "changed_files"
        )
        or pull_request.get(
            "files"
        )
        or pull_request.get(
            "changedFiles"
        )
        or []
    )

    if not isinstance(
        raw_files,
        list,
    ):
        raw_files = []

    changed_files: list[
        dict[str, Any]
    ] = []

    total_additions = 0
    total_deletions = 0
    total_changes = 0

    for raw_file in raw_files:

        if not isinstance(
            raw_file,
            dict,
        ):
            continue

        additions = int(
            raw_file.get(
                "additions",
                0,
            )
            or 0
        )

        deletions = int(
            raw_file.get(
                "deletions",
                0,
            )
            or 0
        )

        changes = int(
            raw_file.get(
                "changes",
                0,
            )
            or 0
        )

        changed_files.append(
            {
                "filename": raw_file.get(
                    "filename"
                ),
                "status": raw_file.get(
                    "status"
                ),
                "additions": additions,
                "deletions": deletions,
                "changes": changes,
                "patch": raw_file.get(
                    "patch"
                ),
            }
        )

        total_additions += additions
        total_deletions += deletions
        total_changes += changes

    changed_files.sort(
        key=lambda item: (
            item.get(
                "filename"
            )
            or ""
        )
    )

    snapshot = {
        "pullRequestNumber": number,
        "owner": owner,
        "repository": repository,
        "title": pull_request.get(
            "title"
        ),
        "sourceBranch": head.get(
            "ref"
        ),
        "targetBranch": base.get(
            "ref"
        ),
        "headSha": head.get(
            "sha"
        ),
        "changedFiles": changed_files,
        "totalAdditions": total_additions,
        "totalDeletions": total_deletions,
        "totalChanges": total_changes,
    }

    return snapshot


# ============================================================
# SNAPSHOT VALIDATION
# ============================================================

def validate_snapshot(
    snapshot: dict[str, Any],
) -> None:

    required_fields = {
        "pullRequestNumber",
        "owner",
        "repository",
        "title",
        "sourceBranch",
        "targetBranch",
        "headSha",
        "changedFiles",
        "totalAdditions",
        "totalDeletions",
        "totalChanges",
    }

    missing = (
        required_fields
        - snapshot.keys()
    )

    if missing:
        raise ValueError(
            "ChangeSnapshot missing fields: "
            + ", ".join(
                sorted(missing)
            )
        )

    if not isinstance(
        snapshot["changedFiles"],
        list,
    ):
        raise ValueError(
            "ChangeSnapshot.changedFiles "
            "must be a list."
        )

    for file_record in snapshot[
        "changedFiles"
    ]:

        if not isinstance(
            file_record,
            dict,
        ):
            raise ValueError(
                "ChangedFile must be "
                "an object."
            )

        required_file_fields = {
            "filename",
            "status",
            "additions",
            "deletions",
            "changes",
            "patch",
        }

        missing_file_fields = (
            required_file_fields
            - file_record.keys()
        )

        if missing_file_fields:
            raise ValueError(
                "ChangedFile missing fields: "
                + ", ".join(
                    sorted(
                        missing_file_fields
                    )
                )
            )


# ============================================================
# EXISTING PYTHON FEATURE PIPELINE
# ============================================================

def discover_feature_pipeline() -> dict[str, Any]:

    if str(AI_SERVICE_DIR) not in sys.path:
        sys.path.insert(
            0,
            str(AI_SERVICE_DIR),
        )

    pipeline: dict[str, Any] = {}

    # --------------------------------------------------------
    # FeatureExtractor
    # --------------------------------------------------------

    try:

        from app.features.extractor import (
            FeatureExtractor,
        )

        pipeline[
            "FeatureExtractor"
        ] = FeatureExtractor

    except Exception as exc:

        pipeline[
            "extractor_error"
        ] = (
            f"{type(exc).__name__}: "
            f"{exc}"
        )

    # --------------------------------------------------------
    # InputMapper
    # --------------------------------------------------------

    try:

        from app.features.input_mapper import (
            InputMapper,
        )

        pipeline[
            "InputMapper"
        ] = InputMapper

    except Exception as exc:

        pipeline[
            "mapper_error"
        ] = (
            f"{type(exc).__name__}: "
            f"{exc}"
        )

    # --------------------------------------------------------
    # FeatureNormalizer
    # --------------------------------------------------------

    try:

        from app.features.normalizer import (
            FeatureNormalizer,
        )

        pipeline[
            "FeatureNormalizer"
        ] = FeatureNormalizer

    except Exception as exc:

        pipeline[
            "normalizer_error"
        ] = (
            f"{type(exc).__name__}: "
            f"{exc}"
        )

    return pipeline


def execute_feature_extraction(
    snapshot: dict[str, Any],
    findings: list[dict[str, Any]],
    pipeline: dict[str, Any],
) -> Any:

    extractor_class = pipeline.get(
        "FeatureExtractor"
    )

    if extractor_class is None:
        raise RuntimeError(
            "Existing FeatureExtractor could "
            "not be imported.\n"
            f"Import error: "
            f"{pipeline.get('extractor_error')}"
        )

    extractor = extractor_class()

    extract_method = getattr(
        extractor,
        "extract",
        None,
    )

    if not callable(
        extract_method
    ):
        raise RuntimeError(
            "FeatureExtractor.extract() "
            "does not exist."
        )

    # --------------------------------------------------------
    # Current project contract:
    #
    # extract({
    #     "changeSnapshot": snapshot,
    #     "findings": findings
    # })
    #
    # The old tests in the project had a stale two-argument
    # call. The current builder must use the current API.
    # --------------------------------------------------------

    feature_input = {
        "changeSnapshot": snapshot,
        "findings": findings,
    }

    mapper_class = pipeline.get("InputMapper")
    if mapper_class is not None:
        mapped_input = mapper_class.from_dict(feature_input)
    else:
        mapped_input = feature_input

    try:
        extracted = extract_method(
            mapped_input
        )
    except (TypeError, AttributeError):
        extracted = extract_method(
            feature_input
        )

    if extracted is None:
        raise RuntimeError(
            "FeatureExtractor returned None."
        )

    return extracted


def execute_normalization(
    features: Any,
    pipeline: dict[str, Any],
) -> Any:

    normalizer_class = pipeline.get(
        "FeatureNormalizer"
    )

    if normalizer_class is None:
        raise RuntimeError(
            "Existing FeatureNormalizer could "
            "not be imported.\n"
            f"Import error: "
            f"{pipeline.get('normalizer_error')}"
        )

    normalizer = normalizer_class()

    normalize_method = getattr(
        normalizer,
        "normalize",
        None,
    )

    if not callable(
        normalize_method
    ):
        raise RuntimeError(
            "FeatureNormalizer.normalize() "
            "does not exist."
        )

    normalized = normalize_method(
        features
    )

    if normalized is None:
        raise RuntimeError(
            "FeatureNormalizer returned None."
        )

    return normalized


# ============================================================
# FEATURE VALIDATION
# ============================================================

def convert_features_to_jsonable(
    value: Any,
) -> Any:

    # Dataclass support
    if hasattr(
        value,
        "__dataclass_fields__",
    ):
        from dataclasses import asdict

        return asdict(value)

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): convert_features_to_jsonable(
                item
            )
            for key, item in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            convert_features_to_jsonable(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return [
            convert_features_to_jsonable(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        (str, int, float, bool),
    ) or value is None:
        return value

    # Pydantic-like objects
    model_dump = getattr(
        value,
        "model_dump",
        None,
    )

    if callable(model_dump):
        return convert_features_to_jsonable(
            model_dump()
        )

    # Object with to_dict
    to_dict = getattr(
        value,
        "to_dict",
        None,
    )

    if callable(to_dict):
        return convert_features_to_jsonable(
            to_dict()
        )

    raise TypeError(
        "Feature object is not JSON serializable: "
        f"{type(value).__name__}"
    )


def validate_features(
    features: Any,
) -> dict[str, Any]:

    normalized = (
        convert_features_to_jsonable(
            features
        )
    )

    if not isinstance(
        normalized,
        dict,
    ):
        raise ValueError(
            "Normalized feature output must "
            "be a JSON object."
        )

    # --------------------------------------------------------
    # The feature pipeline may wrap the actual vector in a
    # FeatureVector schema object.
    # --------------------------------------------------------

    candidate = normalized

    if isinstance(
        normalized.get(
            "features"
        ),
        dict,
    ):
        candidate = normalized[
            "features"
        ]

    elif isinstance(
        normalized.get(
            "featureVector"
        ),
        dict,
    ):
        candidate = normalized[
            "featureVector"
        ]

    elif isinstance(
        normalized.get(
            "feature_vector"
        ),
        dict,
    ):
        candidate = normalized[
            "feature_vector"
        ]

    if not candidate:
        raise ValueError(
            "Normalized feature vector is empty."
        )

    # Validate all actual feature values.
    for key, value in candidate.items():

        if isinstance(
            value,
            bool,
        ):
            continue

        if not isinstance(
            value,
            (int, float),
        ):
            continue

        if isinstance(
            value,
            float,
        ):
            if value != value:
                raise ValueError(
                    f"Feature '{key}' is NaN."
                )

            if value in {
                float("inf"),
                float("-inf"),
            }:
                raise ValueError(
                    f"Feature '{key}' is infinite."
                )

    return normalized


# ============================================================
# DETERMINISTIC NORMALIZATION
# ============================================================

def validate_deterministic_normalization(
    snapshot: dict[str, Any],
    findings: list[dict[str, Any]],
    pipeline: dict[str, Any],
) -> dict[str, Any]:

    first_extracted = (
        execute_feature_extraction(
            snapshot,
            findings,
            pipeline,
        )
    )

    first_normalized = (
        execute_normalization(
            first_extracted,
            pipeline,
        )
    )

    second_extracted = (
        execute_feature_extraction(
            snapshot,
            findings,
            pipeline,
        )
    )

    second_normalized = (
        execute_normalization(
            second_extracted,
            pipeline,
        )
    )

    first_json = (
        convert_features_to_jsonable(
            first_normalized
        )
    )

    second_json = (
        convert_features_to_jsonable(
            second_normalized
        )
    )

    first_serialized = json.dumps(
        first_json,
        ensure_ascii=False,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )

    second_serialized = json.dumps(
        second_json,
        ensure_ascii=False,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )

    if first_serialized != second_serialized:
        raise RuntimeError(
            "Feature normalization is NOT "
            "deterministic."
        )

    return validate_features(
        first_normalized
    )


# ============================================================
# BACKEND ANALYZER CLIENT
# ============================================================

class BackendAnalyzerClient:

    def __init__(
        self,
        endpoint: str,
    ) -> None:

        self.endpoint = endpoint

        self.session = (
            requests.Session()
        )

        self.session.headers.update(
            {
                "Accept": (
                    "application/json"
                ),
                "Content-Type": (
                    "application/json"
                ),
                "User-Agent": (
                    "ReleaseGuard-RealDataset"
                ),
            }
        )

    def analyze(
        self,
        owner: str | dict[str, Any],
        repository: str | None = None,
        number: int | None = None,
        snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        if isinstance(owner, dict):
            payload = owner
        elif snapshot is not None:
            payload = snapshot
        else:
            payload = {
                "owner": owner,
                "repository": repository,
                "pullRequestNumber": number,
            }

        last_error: Exception | None = None

        for attempt in range(
            1,
            MAX_RETRIES + 1,
        ):

            try:

                response = (
                    self.session.post(
                        self.endpoint,
                        json=payload,
                        timeout=(
                            HTTP_TIMEOUT_SECONDS
                        ),
                    )
                )

                if response.status_code == 200:
                    data = response.json()

                    if not isinstance(
                        data,
                        dict,
                    ):
                        raise RuntimeError(
                            "Backend returned "
                            "non-object JSON."
                        )

                    return data

                if response.status_code in {
                    500,
                    502,
                    503,
                    504,
                }:

                    wait_seconds = min(
                        2 ** (attempt - 1),
                        30,
                    )

                    print(
                        "Backend temporary "
                        f"error {response.status_code}; "
                        f"retrying in "
                        f"{wait_seconds}s..."
                    )

                    time.sleep(
                        wait_seconds
                    )

                    continue

                body = response.text[
                    :1000
                ]

                raise RuntimeError(
                    "Backend analysis failed: "
                    f"HTTP {response.status_code}: "
                    f"{body}"
                )

            except (
                requests.RequestException
            ) as exc:

                last_error = exc

                if attempt >= MAX_RETRIES:
                    break

                wait_seconds = min(
                    2 ** (attempt - 1),
                    30,
                )

                print(
                    "Backend request failed: "
                    f"{exc}. Retrying in "
                    f"{wait_seconds}s..."
                )

                time.sleep(
                    wait_seconds
                )

        raise RuntimeError(
            "Backend analyzer request failed "
            f"after {MAX_RETRIES} attempts."
        ) from last_error


# ============================================================
# FINDINGS
# ============================================================

def extract_findings(
    response: dict[str, Any],
) -> list[dict[str, Any]]:

    findings = response.get(
        "findings"
    )

    if findings is None:
        raise RuntimeError(
            "Backend analysis response does "
            "not contain 'findings'."
        )

    if not isinstance(
        findings,
        list,
    ):
        raise RuntimeError(
            "Backend 'findings' must be "
            "a list."
        )

    result: list[
        dict[str, Any]
    ] = []

    for finding in findings:

        if not isinstance(
            finding,
            dict,
        ):
            raise RuntimeError(
                "Backend returned a non-object "
                "finding."
            )

        result.append(
            finding
        )

    return result


# ============================================================
# BACKEND SNAPSHOT CONSISTENCY
# ============================================================

def canonical_json(
    value: Any,
) -> str:

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )


def validate_backend_snapshot(
    local_snapshot: dict[str, Any],
    response: dict[str, Any],
) -> dict[str, Any]:

    backend_snapshot = response.get(
        "snapshot"
    )

    if not isinstance(
        backend_snapshot,
        dict,
    ):
        raise RuntimeError(
            "Backend response does not contain "
            "a valid snapshot."
        )

    # Compare the complete snapshot.
    #
    # This prevents the backend analyzer from
    # silently analyzing a different GitHub
    # representation than the frozen raw data.
    if (
        canonical_json(
            local_snapshot
        )
        != canonical_json(
            backend_snapshot
        )
    ):
        raise RuntimeError(
            "Backend ChangeSnapshot does not "
            "match the snapshot generated from "
            "the frozen real dataset."
        )

    return backend_snapshot


# ============================================================
# LABEL LOADING
# ============================================================

def load_labels() -> dict[
    tuple[str, str, int],
    dict[str, Any],
]:

    if not LABEL_FILE.exists():
        raise FileNotFoundError(
            f"Label file not found: "
            f"{LABEL_FILE}"
        )

    labels: dict[
        tuple[str, str, int],
        dict[str, Any],
    ] = {}

    records = read_jsonl(
        LABEL_FILE
    )

    for index, record in enumerate(
        records,
        start=1,
    ):

        pull_request = record.get(
            "pull_request"
        )

        if not isinstance(
            pull_request,
            dict,
        ):
            raise ValueError(
                "Invalid label record "
                f"at line {index}: "
                "missing pull_request."
            )

        owner = pull_request.get(
            "owner"
        )

        repository = (
            pull_request.get(
                "repository"
            )
        )

        number = pull_request.get(
            "number"
        )

        if not owner or not repository:
            raise ValueError(
                "Invalid label identity "
                f"at line {index}."
            )

        if number is None:
            raise ValueError(
                "Invalid label PR number "
                f"at line {index}."
            )

        key = (
            str(owner),
            str(repository),
            int(number),
        )

        if key in labels:
            raise ValueError(
                "Duplicate label for "
                f"{key}."
            )

        labels[key] = record

    return labels


# ============================================================
# SIGNAL LOADING
# ============================================================

def load_signals() -> dict[
    tuple[str, str, int],
    dict[str, Any],
]:

    if not SIGNAL_DIR.exists():
        raise FileNotFoundError(
            f"Signal directory not found: "
            f"{SIGNAL_DIR}"
        )

    signals: dict[
        tuple[str, str, int],
        dict[str, Any],
    ] = {}

    for path in sorted(
        SIGNAL_DIR.rglob(
            "pr-*.json"
        )
    ):

        record = load_json(
            path
        )

        pull_request = record.get(
            "pull_request"
        )

        if not isinstance(
            pull_request,
            dict,
        ):
            continue

        owner = pull_request.get(
            "owner"
        )

        repository = (
            pull_request.get(
                "repository"
            )
        )

        number = pull_request.get(
            "number"
        )

        if (
            not owner
            or not repository
            or number is None
        ):
            continue

        key = (
            str(owner),
            str(repository),
            int(number),
        )

        if key in signals:
            raise ValueError(
                "Duplicate signal record "
                f"for {key}."
            )

        signals[key] = record

    return signals


# ============================================================
# LABEL EXTRACTION
# ============================================================

def get_label(
    label_record: dict[str, Any],
) -> str:

    outcome = label_record.get(
        "outcome"
    )

    if not isinstance(
        outcome,
        dict,
    ):
        raise ValueError(
            "Label record has no "
            "valid outcome object."
        )

    label = outcome.get(
        "label"
    )

    if label not in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }:
        raise ValueError(
            f"Invalid label: {label}"
        )

    return str(label)


# ============================================================
# FEATURE RECORD
# ============================================================

def build_feature_record(
    snapshot: dict[str, Any],
    findings: list[dict[str, Any]],
    label_record: dict[str, Any],
    signal_record: dict[str, Any],
    normalized_features: dict[str, Any],
) -> dict[str, Any]:

    label = get_label(
        label_record
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_version": TARGET_DATASET_VERSION,
        "source_dataset_version": (
            SOURCE_DATASET_VERSION
        ),
        "feature_version": FEATURE_VERSION,

        "pull_request": {
            "owner": snapshot[
                "owner"
            ],
            "repository": snapshot[
                "repository"
            ],
            "number": snapshot[
                "pullRequestNumber"
            ],
        },

        "change_snapshot": snapshot,

        "findings": findings,

        "features": normalized_features,

        "outcome": {
            "label": label,
            "ordinal": (
                label_record
                .get("outcome", {})
                .get("ordinal")
            ),
        },

        "post_merge_signal_summary": (
            signal_record.get(
                "signal_summary",
                {},
            )
        ),
    }


# ============================================================
# MAIN
# ============================================================

def build_dataset() -> None:

    print("=" * 70)
    print(
        "ReleaseGuard — Real Feature Dataset Builder"
    )
    print("=" * 70)

    print(
        f"Source dataset : "
        f"{SOURCE_DATASET_VERSION}"
    )

    print(
        f"Target dataset : "
        f"{TARGET_DATASET_VERSION}"
    )

    print(
        f"Feature version: "
        f"{FEATURE_VERSION}"
    )

    print(
        f"Backend        : "
        f"{ANALYSIS_ENDPOINT}"
    )

    print()

    # --------------------------------------------------------
    # Discover source data
    # --------------------------------------------------------

    pr_files = (
        discover_pr_files()
    )

    labels = load_labels()
    signals = load_signals()

    print(
        f"PR records discovered : "
        f"{len(pr_files)}"
    )

    print(
        f"Labels discovered     : "
        f"{len(labels)}"
    )

    print(
        f"Signal records loaded : "
        f"{len(signals)}"
    )

    if len(pr_files) != len(labels):
        raise RuntimeError(
            "PR/label count mismatch: "
            f"{len(pr_files)} PRs vs "
            f"{len(labels)} labels."
        )

    if len(pr_files) != len(signals):
        raise RuntimeError(
            "PR/signal count mismatch: "
            f"{len(pr_files)} PRs vs "
            f"{len(signals)} signals."
        )

    # --------------------------------------------------------
    # Existing Python pipeline
    # --------------------------------------------------------

    pipeline = (
        discover_feature_pipeline()
    )

    if "FeatureExtractor" not in pipeline:
        raise RuntimeError(
            "FeatureExtractor unavailable.\n"
            f"{pipeline.get('extractor_error')}"
        )

    if "FeatureNormalizer" not in pipeline:
        raise RuntimeError(
            "FeatureNormalizer unavailable.\n"
            f"{pipeline.get('normalizer_error')}\n\n"
            "The real feature dataset must NOT "
            "be generated without the project's "
            "existing deterministic normalizer."
        )

    print()
    print(
        "Existing FeatureExtractor: "
        "available"
    )

    print(
        "Existing FeatureNormalizer: "
        "available"
    )

    # --------------------------------------------------------
    # Backend analyzer
    # --------------------------------------------------------

    analyzer_client = (
        BackendAnalyzerClient(
            ANALYSIS_ENDPOINT
        )
    )

    print(
        "Existing ReleaseGuard analyzers: "
        "backend endpoint configured"
    )

    print()

    # --------------------------------------------------------
    # Output records
    # --------------------------------------------------------

    snapshots: list[
        dict[str, Any]
    ] = []

    feature_records: list[
        dict[str, Any]
    ] = []

    errors: list[
        dict[str, Any]
    ] = []

    label_counts = Counter()

    finding_count = 0

    # --------------------------------------------------------
    # Process PRs
    # --------------------------------------------------------

    for index, pr_file in enumerate(
        pr_files,
        start=1,
    ):

        try:

            pr_record = load_json(
                pr_file
            )

            identity = (
                extract_pr_identity(
                    pr_record
                )
            )

            if identity is None:
                raise ValueError(
                    "Could not determine "
                    "PR identity."
                )

            owner, repository, number = (
                identity
            )

            key = (
                owner,
                repository,
                number,
            )

            label_record = labels.get(
                key
            )

            if label_record is None:
                raise RuntimeError(
                    f"Missing label for "
                    f"{owner}/{repository}"
                    f"#{number}"
                )

            signal_record = (
                signals.get(key)
            )

            if signal_record is None:
                raise RuntimeError(
                    f"Missing signal record "
                    f"for {owner}/{repository}"
                    f"#{number}"
                )

            # ------------------------------------------------
            # 1. Build ChangeSnapshot
            # ------------------------------------------------

            snapshot = (
                build_change_snapshot(
                    pr_record
                )
            )

            validate_snapshot(
                snapshot
            )

            # ------------------------------------------------
            # 2. Run EXISTING backend analyzers
            # ------------------------------------------------

            backend_response = (
                analyzer_client.analyze(
                    owner,
                    repository,
                    number,
                    snapshot=snapshot,
                )
            )

            # ------------------------------------------------
            # 3. Verify analyzer used the same snapshot
            # ------------------------------------------------

            validate_backend_snapshot(
                snapshot,
                backend_response,
            )

            # ------------------------------------------------
            # 4. Extract real Finding[]
            # ------------------------------------------------

            findings = (
                extract_findings(
                    backend_response
                )
            )

            finding_count += len(
                findings
            )

            # ------------------------------------------------
            # 5. Existing feature extraction
            # ------------------------------------------------

            normalized_features = (
                validate_deterministic_normalization(
                    snapshot,
                    findings,
                    pipeline,
                )
            )

            # ------------------------------------------------
            # 6. Validate feature schema
            # ------------------------------------------------

            feature_json = (
                convert_features_to_jsonable(
                    normalized_features
                )
            )

            if not isinstance(
                feature_json,
                dict,
            ):
                raise RuntimeError(
                    "Feature vector is not "
                    "a JSON object."
                )

            if len(feature_json) == 0:
                raise RuntimeError(
                    "Feature vector is empty."
                )

            # ------------------------------------------------
            # 7. Build final record
            # ------------------------------------------------

            feature_record = (
                build_feature_record(
                    snapshot,
                    findings,
                    label_record,
                    signal_record,
                    feature_json,
                )
            )

            snapshots.append(
                snapshot
            )

            feature_records.append(
                feature_record
            )

            label = get_label(
                label_record
            )

            label_counts[label] += 1

            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            print(
                f"[{index}/{len(pr_files)}] "
                f"{owner}/{repository}#{number} "
                f"snapshot=OK "
                f"findings={len(findings)} "
                f"features={len(feature_json)} "
                f"label={label}"
            )

            if REQUEST_DELAY_SECONDS > 0:
                time.sleep(
                    REQUEST_DELAY_SECONDS
                )

        except Exception as exc:

            error_record = {
                "index": index,
                "file": str(
                    pr_file
                ),
                "error_type": (
                    type(exc).__name__
                ),
                "error": str(exc),
            }

            errors.append(
                error_record
            )

            print(
                f"[{index}/{len(pr_files)}] "
                f"ERROR: {exc}"
            )

    # --------------------------------------------------------
    # HARD COMPLETENESS CHECK
    # --------------------------------------------------------

    if errors:
        raise RuntimeError(
            "Real feature dataset build "
            f"failed with {len(errors)} errors.\n"
            "No dataset freeze was created."
        )

    if len(snapshots) != len(
        pr_files
    ):
        raise RuntimeError(
            "Snapshot count mismatch."
        )

    if len(feature_records) != len(
        pr_files
    ):
        raise RuntimeError(
            "Feature record count mismatch."
        )

    # --------------------------------------------------------
    # Dataset hash
    # --------------------------------------------------------

    dataset_sha256 = (
        sha256_jsonl(
            feature_records
        )
    )

    snapshot_sha256 = (
        sha256_jsonl(
            snapshots
        )
    )

    # --------------------------------------------------------
    # Write snapshots
    # --------------------------------------------------------

    write_jsonl(
        SNAPSHOT_FILE,
        snapshots,
    )

    # --------------------------------------------------------
    # Write feature dataset
    # --------------------------------------------------------

    write_jsonl(
        FEATURE_FILE,
        feature_records,
    )

    # --------------------------------------------------------
    # Manifest
    # --------------------------------------------------------

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "dataset_version": TARGET_DATASET_VERSION,
        "source_dataset_version": (
            SOURCE_DATASET_VERSION
        ),
        "feature_version": FEATURE_VERSION,

        "created_at_utc": (
            time.strftime(
                "%Y-%m-%dT%H:%M:%SZ",
                time.gmtime(),
            )
        ),

        "source": {
            "raw_pr_directory": str(
                RAW_PR_DIR
            ),
            "label_file": str(
                LABEL_FILE
            ),
            "signal_directory": str(
                SIGNAL_DIR
            ),
        },

        "pipeline": {
            "change_snapshot": (
                "EXECUTED"
            ),
            "releaseguard_analyzers": (
                "EXECUTED"
            ),
            "finding_generation": (
                "EXECUTED"
            ),
            "feature_extraction": (
                "EXECUTED"
            ),
            "feature_normalization": (
                "EXECUTED"
            ),
            "deterministic_normalization": (
                "VALIDATED"
            ),
            "feature_schema_validation": (
                "VALIDATED"
            ),
        },

        "backend": {
            "analysis_endpoint": (
                ANALYSIS_ENDPOINT
            ),
        },

        "records": {
            "pr_records": len(
                pr_files
            ),
            "snapshots": len(
                snapshots
            ),
            "feature_records": len(
                feature_records
            ),
            "findings_total": (
                finding_count
            ),
            "errors": len(
                errors
            ),
        },

        "label_distribution": {
            label: label_counts.get(
                label,
                0,
            )
            for label in (
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
            )
        },

        "hashes": {
            "snapshot_dataset_sha256": (
                snapshot_sha256
            ),
            "feature_dataset_sha256": (
                dataset_sha256
            ),
        },

        "output": {
            "change_snapshots": str(
                SNAPSHOT_FILE
            ),
            "feature_dataset": str(
                FEATURE_FILE
            ),
            "manifest": str(
                MANIFEST_FILE
            ),
        },

        "errors": errors,
    }

    write_json(
        MANIFEST_FILE,
        manifest,
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "REAL FEATURE DATASET BUILD COMPLETE"
    )
    print("=" * 70)

    print(
        f"PR records discovered : "
        f"{len(pr_files)}"
    )

    print(
        f"Snapshots generated   : "
        f"{len(snapshots)}"
    )

    print(
        f"Analyzer executions   : "
        f"{len(snapshots)}"
    )

    print(
        f"Finding records total : "
        f"{finding_count}"
    )

    print(
        f"Feature records       : "
        f"{len(feature_records)}"
    )

    print(
        "Feature extraction    : "
        "EXECUTED"
    )

    print(
        "Feature normalization : "
        "EXECUTED"
    )

    print(
        "Determinism check     : "
        "PASSED"
    )

    print(
        "Schema validation     : "
        "PASSED"
    )

    print(
        "Errors                : "
        f"{len(errors)}"
    )

    print()
    print(
        "Label distribution:"
    )

    for label in (
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ):

        count = label_counts.get(
            label,
            0,
        )

        percentage = (
            count
            / len(feature_records)
            * 100
        )

        print(
            f"  {label:<9} "
            f"{count:>5} "
            f"({percentage:6.2f}%)"
        )

    print()
    print(
        "Feature dataset:"
    )

    print(
        f"  {FEATURE_FILE}"
    )

    print(
        "Change snapshots:"
    )

    print(
        f"  {SNAPSHOT_FILE}"
    )

    print(
        "Manifest:"
    )

    print(
        f"  {MANIFEST_FILE}"
    )

    print()
    print(
        "Dataset SHA-256:"
    )

    print(
        f"  {dataset_sha256}"
    )

    print("=" * 70)


if __name__ == "__main__":
    build_dataset()