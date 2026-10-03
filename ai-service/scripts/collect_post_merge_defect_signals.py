from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


# ============================================================
# PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = AI_SERVICE_DIR.parent

ENV_FILE = PROJECT_ROOT / ".env"

DATA_DIR = AI_SERVICE_DIR / "data" / "real"
RAW_DIR = DATA_DIR / "raw"

PR_RAW_DIR = RAW_DIR / "pull_requests"
LINKED_ISSUES_RAW_DIR = RAW_DIR / "linked_issues"
DEFECT_RAW_DIR = RAW_DIR / "post_merge_defect_signals"

MANIFEST_DIR = DATA_DIR / "manifests"

COLLECTION_MANIFEST_FILE = (
    MANIFEST_DIR / "post_merge_defect_signal_manifest.json"
)

TIMELINE_CACHE_DIR = (
    RAW_DIR / "_api_cache" / "timelines"
)


# ============================================================
# CONFIGURATION
# ============================================================

GITHUB_API = "https://api.github.com"

API_VERSION = "2022-11-28"

REQUEST_TIMEOUT = 60

# Conservative ordinary REST API pacing.
REQUEST_DELAY_SECONDS = 0.25

MAX_RETRIES = 5

DATASET_VERSION = "1.0.0-real"

SCHEMA_VERSION = "1.0.0"

COLLECTOR_VERSION = "2.0.0"


# ============================================================
# DEFECT LABELS
# ============================================================

DEFECT_LABEL_TERMS = {
    "bug",
    "bugs",
    "defect",
    "defects",
    "regression",
    "regressions",
    "bugfix",
    "bug-fix",
    "bug fix",
    "regression-fix",
    "regression fix",
    "type: bug",
    "type:bug",
    "kind/bug",
    "kind: bug",
    "issue: bug",
    "issue/bug",
}


DEFECT_TITLE_TERMS = {
    "fix",
    "bug",
    "regression",
    "revert",
    "hotfix",
}


# ============================================================
# ENVIRONMENT
# ============================================================

def load_env_file() -> None:
    if not ENV_FILE.exists():
        return

    for raw_line in ENV_FILE.read_text(
        encoding="utf-8"
    ).splitlines():

        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


def get_github_token() -> str:
    load_env_file()

    token = (
        os.getenv("GITHUB_TOKEN")
        or os.getenv("GITHUB_TOKEN_READONLY")
        or os.getenv("RELEASEGUARD_GITHUB_TOKEN")
        or os.getenv("GH_TOKEN")
    )

    if not token:
        raise RuntimeError(
            "GitHub token not found. "
            "Expected GITHUB_TOKEN in the project root .env file."
        )

    return token


# ============================================================
# HTTP CLIENT
# ============================================================

class GitHubRateLimitError(RuntimeError):
    """Raised when GitHub rate limiting prevents collection."""


class GitHubClient:

    def __init__(self, token: str):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": (
                    "ReleaseGuard-RealDataset/"
                    f"{COLLECTOR_VERSION}"
                ),
            }
        )

        self.rate_limit_events = 0

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:

        url = (
            path
            if path.startswith("http")
            else f"{GITHUB_API}{path}"
        )

        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):

            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )

                remaining = response.headers.get(
                    "X-RateLimit-Remaining"
                )

                reset = response.headers.get(
                    "X-RateLimit-Reset"
                )

                # ------------------------------------------------
                # Primary rate limit
                # ------------------------------------------------

                if response.status_code in {403, 429}:

                    self.rate_limit_events += 1

                    retry_after = response.headers.get(
                        "Retry-After"
                    )

                    if retry_after:
                        try:
                            wait_seconds = max(
                                int(float(retry_after)) + 1,
                                1,
                            )
                        except ValueError:
                            wait_seconds = 60

                    elif reset:
                        try:
                            wait_seconds = max(
                                int(reset)
                                - int(time.time())
                                + 2,
                                2,
                            )
                        except ValueError:
                            wait_seconds = 60

                    else:
                        wait_seconds = min(
                            30 * attempt,
                            300,
                        )

                    print(
                        f"GitHub rate limit encountered. "
                        f"Remaining={remaining}. "
                        f"Waiting {wait_seconds}s..."
                    )

                    time.sleep(wait_seconds)
                    continue

                # ------------------------------------------------
                # Secondary/server throttling
                # ------------------------------------------------

                if response.status_code in {
                    500,
                    502,
                    503,
                    504,
                }:

                    wait_seconds = min(
                        2 ** attempt,
                        60,
                    )

                    print(
                        f"GitHub returned "
                        f"{response.status_code}. "
                        f"Retrying in {wait_seconds}s..."
                    )

                    time.sleep(wait_seconds)
                    continue

                response.raise_for_status()

                time.sleep(REQUEST_DELAY_SECONDS)

                return response

            except requests.RequestException as exc:

                last_error = exc

                if attempt == MAX_RETRIES:
                    break

                wait_seconds = min(
                    2 ** attempt,
                    60,
                )

                print(
                    f"Request failed: {exc}. "
                    f"Retrying in {wait_seconds}s..."
                )

                time.sleep(wait_seconds)

        raise RuntimeError(
            f"GitHub request failed after "
            f"{MAX_RETRIES} attempts: {url}"
        ) from last_error


# ============================================================
# FILE HELPERS
# ============================================================

def ensure_directories() -> None:

    DEFECT_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    TIMELINE_CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def atomic_write_json(
    path: Path,
    data: Any,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary_path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temporary_path.replace(path)


def load_json(path: Path) -> Any:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# DATETIME
# ============================================================

def parse_github_datetime(
    value: str | None,
) -> datetime | None:

    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    except ValueError:
        return None


def utc_now() -> str:

    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


# ============================================================
# PR DISCOVERY
# ============================================================

def discover_pr_files() -> list[Path]:

    if not PR_RAW_DIR.exists():

        raise FileNotFoundError(
            f"PR raw directory not found: "
            f"{PR_RAW_DIR}"
        )

    files = sorted(
        PR_RAW_DIR.rglob("pr-*.json")
    )

    if not files:

        raise FileNotFoundError(
            f"No PR records found under: "
            f"{PR_RAW_DIR}"
        )

    return files


# ============================================================
# PR IDENTITY
# ============================================================

def extract_pr_identity(
    payload: dict[str, Any],
) -> tuple[str, str, int] | None:

    repository = payload.get(
        "repository",
        {},
    )

    pull_request = payload.get(
        "pull_request",
        {},
    )

    if not isinstance(repository, dict):
        return None

    if not isinstance(pull_request, dict):
        return None

    full_name = repository.get(
        "full_name"
    )

    number = pull_request.get(
        "number"
    )

    if not full_name or number is None:
        return None

    if "/" not in full_name:
        return None

    owner, repo = full_name.split(
        "/",
        1,
    )

    try:
        number = int(number)

    except (
        TypeError,
        ValueError,
    ):
        return None

    return (
        owner,
        repo,
        number,
    )


# ============================================================
# TIMELINE CACHE
# ============================================================

def timeline_cache_path(
    owner: str,
    repo: str,
    pr_number: int,
) -> Path:

    return (
        TIMELINE_CACHE_DIR
        / owner
        / repo
        / f"pr-{pr_number}.json"
    )


def load_cached_timeline(
    owner: str,
    repo: str,
    pr_number: int,
) -> list[dict[str, Any]] | None:

    path = timeline_cache_path(
        owner,
        repo,
        pr_number,
    )

    if not path.exists():
        return None

    try:

        data = load_json(path)

        if isinstance(data, list):

            return [
                item
                for item in data
                if isinstance(item, dict)
            ]

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return None

    return None


def save_cached_timeline(
    owner: str,
    repo: str,
    pr_number: int,
    events: list[dict[str, Any]],
) -> None:

    path = timeline_cache_path(
        owner,
        repo,
        pr_number,
    )

    atomic_write_json(
        path,
        events,
    )


# ============================================================
# GITHUB TIMELINE
# ============================================================

def fetch_pull_request_timeline(
    client: GitHubClient,
    owner: str,
    repo: str,
    pr_number: int,
) -> list[dict[str, Any]]:

    cached = load_cached_timeline(
        owner,
        repo,
        pr_number,
    )

    if cached is not None:
        return cached

    events: list[dict[str, Any]] = []

    page = 1

    while True:

        response = client.get(
            (
                f"/repos/{owner}/{repo}"
                f"/issues/{pr_number}/timeline"
            ),
            params={
                "per_page": 100,
                "page": page,
            },
        )

        data = response.json()

        if not isinstance(data, list):
            break

        if not data:
            break

        events.extend(
            item
            for item in data
            if isinstance(item, dict)
        )

        if len(data) < 100:
            break

        page += 1

    save_cached_timeline(
        owner,
        repo,
        pr_number,
        events,
    )

    return events


# ============================================================
# LABEL HELPERS
# ============================================================

def normalize_label(
    label: str,
) -> str:

    return (
        label
        .strip()
        .lower()
        .replace("_", " ")
    )


def is_defect_label(
    label: str,
) -> bool:

    normalized = normalize_label(
        label
    )

    if normalized in DEFECT_LABEL_TERMS:
        return True

    return any(
        term in normalized
        for term in {
            "bug",
            "regression",
            "defect",
        }
    )


def extract_labels(
    item: dict[str, Any],
) -> list[str]:

    labels = item.get(
        "labels",
        [],
    )

    if not isinstance(labels, list):
        return []

    result: list[str] = []

    for label in labels:

        if isinstance(
            label,
            dict,
        ):

            name = label.get(
                "name"
            )

            if name:
                result.append(
                    str(name)
                )

        elif isinstance(
            label,
            str,
        ):

            result.append(label)

    return result


# ============================================================
# TEXT / REFERENCE HELPERS
# ============================================================

def find_pr_references(
    text: str,
    owner: str,
    repo: str,
    pr_number: int,
) -> bool:

    if not text:
        return False

    patterns = [
        rf"\b#{pr_number}\b",
        rf"\b{re.escape(owner)}/{re.escape(repo)}#{pr_number}\b",
        rf"/pull/{pr_number}\b",
    ]

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def extract_event_text(
    event: dict[str, Any],
) -> str:

    parts: list[str] = []

    for key in (
        "body",
        "title",
        "message",
        "commit_message",
    ):

        value = event.get(key)

        if isinstance(value, str):
            parts.append(value)

    commit = event.get(
        "commit",
        {},
    )

    if isinstance(commit, dict):

        message = commit.get(
            "message"
        )

        if isinstance(
            message,
            str,
        ):
            parts.append(message)

    source = event.get(
        "source",
        {},
    )

    if isinstance(source, dict):

        source_issue = source.get(
            "issue",
            {},
        )

        if isinstance(
            source_issue,
            dict,
        ):

            title = source_issue.get(
                "title"
            )

            body = source_issue.get(
                "body"
            )

            if isinstance(
                title,
                str,
            ):
                parts.append(title)

            if isinstance(
                body,
                str,
            ):
                parts.append(body)

    return "\n".join(parts)


# ============================================================
# LINKED ISSUE CACHE
# ============================================================

def load_linked_issue_records(
    owner: str,
    repo: str,
) -> list[dict[str, Any]]:

    directory = (
        LINKED_ISSUES_RAW_DIR
        / owner
        / repo
    )

    if not directory.exists():
        return []

    records: list[dict[str, Any]] = []

    for path in directory.glob(
        "*.json"
    ):

        try:

            payload = load_json(path)

            if isinstance(
                payload,
                dict,
            ):
                records.append(payload)

        except (
            OSError,
            json.JSONDecodeError,
        ):
            continue

    return records


# ============================================================
# SIGNAL COLLECTION — TIMELINE
# ============================================================

def collect_timeline_signals(
    events: list[dict[str, Any]],
    owner: str,
    repo: str,
    pr_number: int,
    merged_at: str,
) -> list[dict[str, Any]]:

    signals: list[dict[str, Any]] = []

    merge_time = parse_github_datetime(
        merged_at
    )

    for event in events:

        event_time = parse_github_datetime(
            event.get("created_at")
            or event.get("updated_at")
        )

        if (
            merge_time
            and event_time
            and event_time <= merge_time
        ):
            continue

        event_type = event.get(
            "event"
        ) or event.get(
            "type"
        )

        text = extract_event_text(
            event
        )

        text_lower = text.lower()

        # ----------------------------------------------------
        # Explicit revert evidence
        # ----------------------------------------------------

        if (
            event_type == "committed"
            and "revert" in text_lower
        ):

            signals.append(
                {
                    "signal_type": (
                        "explicit_revert_commit"
                    ),
                    "strength": "strong",
                    "commit_sha": event.get(
                        "sha"
                    ) or event.get(
                        "commit_id"
                    ),
                    "commit_url": event.get(
                        "html_url"
                    ),
                    "message": text,
                    "observed_at": (
                        event.get("created_at")
                        or event.get("updated_at")
                    ),
                    "reason": (
                        "A post-merge timeline commit "
                        "contains explicit revert evidence."
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # Cross-referenced issue / PR
        # ----------------------------------------------------

        if event_type not in {
            "cross-referenced",
            "connected",
        }:
            continue

        source = event.get(
            "source",
            {},
        )

        if not isinstance(
            source,
            dict,
        ):
            continue

        source_issue = source.get(
            "issue",
            {},
        )

        if not isinstance(
            source_issue,
            dict,
        ):
            continue

        title = source_issue.get(
            "title"
        ) or ""

        body = source_issue.get(
            "body"
        ) or ""

        labels = extract_labels(
            source_issue
        )

        defect_labels = [
            label
            for label in labels
            if is_defect_label(label)
        ]

        source_number = source_issue.get(
            "number"
        )

        source_url = source_issue.get(
            "html_url"
        )

        source_is_pr = bool(
            source_issue.get(
                "pull_request"
            )
        )

        combined_text = (
            f"{title}\n{body}"
        )

        # Do not classify a cross-reference as evidence
        # unless the source actually refers to this PR.
        if not find_pr_references(
            combined_text,
            owner,
            repo,
            pr_number,
        ):
            continue

        title_lower = title.lower()

        title_signal = any(
            term in title_lower
            for term in DEFECT_TITLE_TERMS
        )

        if defect_labels:

            signal_type = (
                "post_merge_followup_pr"
                if source_is_pr
                else "post_merge_defect_issue"
            )

            strength = (
                "moderate"
                if source_is_pr
                else "strong"
            )

            signals.append(
                {
                    "signal_type": signal_type,
                    "strength": strength,
                    "issue_number": source_number,
                    "issue_url": source_url,
                    "title": title,
                    "body": body,
                    "labels": labels,
                    "defect_labels": defect_labels,
                    "created_at": source_issue.get(
                        "created_at"
                    ),
                    "closed_at": source_issue.get(
                        "closed_at"
                    ),
                    "reason": (
                        "A post-merge referenced "
                        "issue/PR explicitly references "
                        "the original PR and carries "
                        "defect-oriented labeling."
                    ),
                }
            )

        elif title_signal:

            signal_type = (
                "post_merge_followup_pr"
                if source_is_pr
                else "post_merge_referenced_issue"
            )

            strength = (
                "moderate"
                if source_is_pr
                else "weak"
            )

            signals.append(
                {
                    "signal_type": signal_type,
                    "strength": strength,
                    "issue_number": source_number,
                    "issue_url": source_url,
                    "title": title,
                    "body": body,
                    "labels": labels,
                    "created_at": source_issue.get(
                        "created_at"
                    ),
                    "closed_at": source_issue.get(
                        "closed_at"
                    ),
                    "reason": (
                        "A post-merge referenced "
                        "issue/PR explicitly references "
                        "the original PR and contains "
                        "defect/fix-oriented wording."
                    ),
                }
            )

    return signals


# ============================================================
# SIGNAL COLLECTION — ALREADY COLLECTED LINKED ISSUES
# ============================================================

def collect_cached_issue_signals(
    owner: str,
    repo: str,
    pr_number: int,
    merged_at: str,
) -> list[dict[str, Any]]:

    records = load_linked_issue_records(
        owner,
        repo,
    )

    if not records:
        return []

    signals: list[dict[str, Any]] = []

    merge_time = parse_github_datetime(
        merged_at
    )

    for record in records:

        issue = record.get(
            "issue",
            record,
        )

        if not isinstance(
            issue,
            dict,
        ):
            continue

        issue_number = issue.get(
            "number"
        )

        if issue_number is None:
            continue

        title = issue.get(
            "title"
        ) or ""

        body = issue.get(
            "body"
        ) or ""

        created_at = issue.get(
            "created_at"
        )

        created_time = parse_github_datetime(
            created_at
        )

        # Only post-merge issues belong here.
        if (
            merge_time
            and created_time
            and created_time <= merge_time
        ):
            continue

        labels = extract_labels(
            issue
        )

        defect_labels = [
            label
            for label in labels
            if is_defect_label(label)
        ]

        if not find_pr_references(
            f"{title}\n{body}",
            owner,
            repo,
            pr_number,
        ):
            continue

        if defect_labels:

            signals.append(
                {
                    "signal_type": (
                        "post_merge_defect_issue"
                    ),
                    "strength": "strong",
                    "issue_number": issue_number,
                    "issue_url": issue.get(
                        "html_url"
                    ),
                    "title": title,
                    "state": issue.get(
                        "state"
                    ),
                    "created_at": created_at,
                    "closed_at": issue.get(
                        "closed_at"
                    ),
                    "labels": labels,
                    "defect_labels": defect_labels,
                    "reason": (
                        "Previously collected linked "
                        "issue data contains a post-merge "
                        "issue with defect-oriented labels."
                    ),
                }
            )

    return signals


# ============================================================
# DEDUPLICATION
# ============================================================

def signal_identity(
    signal: dict[str, Any],
) -> tuple[Any, ...]:

    return (
        signal.get("signal_type"),
        signal.get("commit_sha"),
        signal.get("issue_number"),
        signal.get("pull_request_number"),
        signal.get("issue_url"),
        signal.get("pull_request_url"),
    )


def deduplicate_signals(
    signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    result: list[dict[str, Any]] = []

    seen: set[tuple[Any, ...]] = set()

    for signal in signals:

        identity = signal_identity(
            signal
        )

        if identity in seen:
            continue

        seen.add(identity)
        result.append(signal)

    return result


# ============================================================
# BUILD RECORD
# ============================================================

def collect_signals_for_pr(
    client: GitHubClient,
    pr_payload: dict[str, Any],
) -> dict[str, Any] | None:

    identity = extract_pr_identity(
        pr_payload
    )

    if identity is None:
        return None

    owner, repo, pr_number = identity

    repository = pr_payload.get(
        "repository",
        {},
    )

    pull_request = pr_payload.get(
        "pull_request",
        {},
    )

    merged_at = pull_request.get(
        "merged_at"
    )

    base_record = {
        "schema_version": SCHEMA_VERSION,
        "dataset_type": (
            "releaseguard-real-post-merge-defect-signals"
        ),
        "dataset_version": DATASET_VERSION,
        "collector_version": COLLECTOR_VERSION,
        "collected_at": utc_now(),
        "pull_request": {
            "repository": (
                repository.get("full_name")
                or f"{owner}/{repo}"
            ),
            "owner": owner,
            "name": repo,
            "number": pr_number,
            "id": pull_request.get(
                "id"
            ),
            "html_url": pull_request.get(
                "html_url"
            ),
            "title": pull_request.get(
                "title"
            ),
            "created_at": pull_request.get(
                "created_at"
            ),
            "merged_at": merged_at,
            "merge_commit_sha": pull_request.get(
                "merge_commit_sha"
            ),
        },
        "signals": [],
        "signal_summary": {
            "has_any_signal": False,
            "strong_signal_count": 0,
            "moderate_signal_count": 0,
            "weak_signal_count": 0,
            "total_signal_count": 0,
        },
        "labeling_note": (
            "Post-merge signals are observational "
            "evidence only. They must not be treated "
            "as definitive defect labels without "
            "the V0.5.8 labeling policy."
        ),
    }

    # Unmerged PRs cannot have post-merge evidence.
    if not merged_at:
        return base_record

    signals: list[dict[str, Any]] = []

    # --------------------------------------------------------
    # 1. Existing linked-issue data
    # --------------------------------------------------------

    signals.extend(
        collect_cached_issue_signals(
            owner,
            repo,
            pr_number,
            merged_at,
        )
    )

    # --------------------------------------------------------
    # 2. Timeline-based post-merge evidence
    # --------------------------------------------------------

    events = fetch_pull_request_timeline(
        client,
        owner,
        repo,
        pr_number,
    )

    signals.extend(
        collect_timeline_signals(
            events,
            owner,
            repo,
            pr_number,
            merged_at,
        )
    )

    signals = deduplicate_signals(
        signals
    )

    strong_count = sum(
        1
        for signal in signals
        if signal.get("strength") == "strong"
    )

    moderate_count = sum(
        1
        for signal in signals
        if signal.get("strength") == "moderate"
    )

    weak_count = sum(
        1
        for signal in signals
        if signal.get("strength") == "weak"
    )

    base_record["signals"] = signals

    base_record["signal_summary"] = {
        "has_any_signal": bool(
            signals
        ),
        "strong_signal_count": strong_count,
        "moderate_signal_count": moderate_count,
        "weak_signal_count": weak_count,
        "total_signal_count": len(
            signals
        ),
    }

    return base_record


# ============================================================
# MANIFEST
# ============================================================

def write_manifest(
    pr_files_count: int,
    processed: int,
    skipped_existing: int,
    errors: int,
    error_records: list[dict[str, Any]],
    signal_counts: dict[str, int],
    started_at: float,
    rate_limit_events: int,
) -> None:

    completed_at = time.time()

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "dataset_type": (
            "releaseguard-real-post-merge-defect-signals"
        ),
        "dataset_version": DATASET_VERSION,

        "collection": {
            "access_method": (
                "GitHub REST API"
            ),
            "collector_version": (
                COLLECTOR_VERSION
            ),
            "source_pr_records": (
                pr_files_count
            ),
            "processed_pr_records": (
                processed
            ),
            "skipped_existing": (
                skipped_existing
            ),
            "total_errors": errors,
            "rate_limit_events": (
                rate_limit_events
            ),
            "started_at_unix": (
                started_at
            ),
            "completed_at_unix": (
                completed_at
            ),
            "duration_seconds": (
                completed_at - started_at
            ),
        },

        "signal_counts": signal_counts,

        "storage": {
            "raw_directory": str(
                DEFECT_RAW_DIR
            ),
            "timeline_cache_directory": str(
                TIMELINE_CACHE_DIR
            ),
        },

        "errors": error_records,

        "methodology": {
            "purpose": (
                "Collect post-merge observational "
                "evidence that may indicate defects."
            ),
            "labeling_status": (
                "Signals are not target labels."
            ),
            "strong_signals": [
                "explicit_revert_commit",
                "post_merge_defect_issue",
            ],
            "moderate_signals": [
                "post_merge_followup_pr",
            ],
            "weak_signals": [
                "post_merge_referenced_issue",
            ],
            "api_strategy": (
                "Timeline-based collection with "
                "local caching; GitHub Search API "
                "is intentionally avoided."
            ),
        },
    }

    atomic_write_json(
        COLLECTION_MANIFEST_FILE,
        manifest,
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 70)
    print(
        "ReleaseGuard — Post-Merge Defect Signal Collection"
    )
    print("=" * 70)

    ensure_directories()

    token = get_github_token()

    client = GitHubClient(
        token
    )

    pr_files = discover_pr_files()

    print(
        f"PR records discovered: "
        f"{len(pr_files)}"
    )

    processed = 0
    skipped_existing = 0
    errors = 0

    signal_counts = {
        "explicit_revert_commit": 0,
        "post_merge_defect_issue": 0,
        "post_merge_referenced_issue": 0,
        "post_merge_followup_pr": 0,
    }

    error_records: list[
        dict[str, Any]
    ] = []

    started_at = time.time()

    try:

        for index, pr_file in enumerate(
            pr_files,
            start=1,
        ):

            try:

                pr_payload = load_json(
                    pr_file
                )

                identity = extract_pr_identity(
                    pr_payload
                )

                if identity is None:

                    errors += 1

                    error_records.append(
                        {
                            "pr_file": str(
                                pr_file
                            ),
                            "error": (
                                "Unable to extract "
                                "PR identity."
                            ),
                        }
                    )

                    continue

                owner, repo, pr_number = identity

                destination = (
                    DEFECT_RAW_DIR
                    / owner
                    / repo
                    / f"pr-{pr_number}.json"
                )

                # ------------------------------------------------
                # RESUME SUPPORT
                # ------------------------------------------------

                if destination.exists():

                    skipped_existing += 1

                    print(
                        f"[{index}/{len(pr_files)}] "
                        f"SKIP "
                        f"{owner}/{repo}#{pr_number}"
                    )

                    continue

                print(
                    f"[{index}/{len(pr_files)}] "
                    f"Collecting signals for "
                    f"{owner}/{repo}#{pr_number}"
                )

                record = collect_signals_for_pr(
                    client,
                    pr_payload,
                )

                if record is None:

                    errors += 1

                    error_records.append(
                        {
                            "pr_file": str(
                                pr_file
                            ),
                            "error": (
                                "Could not build "
                                "signal record."
                            ),
                        }
                    )

                    continue

                atomic_write_json(
                    destination,
                    record,
                )

                processed += 1

                for signal in record.get(
                    "signals",
                    [],
                ):

                    signal_type = signal.get(
                        "signal_type"
                    )

                    if signal_type in signal_counts:

                        signal_counts[
                            signal_type
                        ] += 1

                summary = record.get(
                    "signal_summary",
                    {},
                )

                print(
                    f"    signals="
                    f"{summary.get('total_signal_count', 0)} "
                    f"strong="
                    f"{summary.get('strong_signal_count', 0)} "
                    f"moderate="
                    f"{summary.get('moderate_signal_count', 0)} "
                    f"weak="
                    f"{summary.get('weak_signal_count', 0)}"
                )

            except KeyboardInterrupt:

                raise

            except Exception as exc:

                errors += 1

                error_records.append(
                    {
                        "pr_file": str(
                            pr_file
                        ),
                        "error": str(exc),
                    }
                )

                print(
                    f"    ERROR: {exc}"
                )

                # Continue to the next PR.
                continue

    except KeyboardInterrupt:

        print()
        print(
            "Collection interrupted by user."
        )
        print(
            "Already-written PR records are "
            "safe and will be skipped on rerun."
        )

    finally:

        write_manifest(
            pr_files_count=len(
                pr_files
            ),
            processed=processed,
            skipped_existing=(
                skipped_existing
            ),
            errors=errors,
            error_records=(
                error_records
            ),
            signal_counts=(
                signal_counts
            ),
            started_at=started_at,
            rate_limit_events=(
                client.rate_limit_events
            ),
        )

    print()
    print("=" * 70)
    print(
        "POST-MERGE DEFECT SIGNAL COLLECTION COMPLETE"
    )
    print("=" * 70)

    print(
        f"PR records discovered: "
        f"{len(pr_files)}"
    )

    print(
        f"PR records processed: "
        f"{processed}"
    )

    print(
        f"Already collected: "
        f"{skipped_existing}"
    )

    print(
        f"Errors: "
        f"{errors}"
    )

    print(
        f"Rate-limit events: "
        f"{client.rate_limit_events}"
    )

    print()
    print(
        "Signal counts:"
    )

    for signal_type, count in (
        signal_counts.items()
    ):

        print(
            f"  {signal_type}: {count}"
        )

    print()
    print(
        "Raw signals:"
    )

    print(
        f"  {DEFECT_RAW_DIR}"
    )

    print()
    print(
        "Timeline cache:"
    )

    print(
        f"  {TIMELINE_CACHE_DIR}"
    )

    print()
    print(
        "Collection manifest:"
    )

    print(
        f"  {COLLECTION_MANIFEST_FILE}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()
