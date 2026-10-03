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
# Paths
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = AI_SERVICE_DIR.parent

ENV_FILE = PROJECT_ROOT / ".env"

DATA_DIR = AI_SERVICE_DIR / "data" / "real"
RAW_DIR = DATA_DIR / "raw"

PR_RAW_DIR = RAW_DIR / "pull_requests"
ISSUE_RAW_DIR = RAW_DIR / "linked_issues"

MANIFEST_DIR = DATA_DIR / "manifests"

COLLECTION_MANIFEST_FILE = (
    MANIFEST_DIR / "linked_issue_collection_manifest.json"
)


# ============================================================
# Configuration
# ============================================================

GITHUB_API = "https://api.github.com"

API_DELAY_SECONDS = 0.15
TIMEOUT_SECONDS = 30

DATASET_VERSION = "1.0.0-real"
SCHEMA_VERSION = "1.0.0"
COLLECTOR_VERSION = "1.1.0"


# ============================================================
# GitHub issue reference patterns
# ============================================================

ISSUE_REFERENCE_PATTERNS = [
    # Explicit cross-repository reference:
    #
    # owner/repository#123
    #
    (
        "cross_repository",
        re.compile(
            r"(?P<owner>[A-Za-z0-9_.-]+)/"
            r"(?P<repository>[A-Za-z0-9_.-]+)"
            r"#(?P<number>\d+)"
        ),
    ),

    # Local repository reference:
    #
    # #123
    #
    (
        "local",
        re.compile(
            r"(?<![\w#])"
            r"#(?P<number>\d+)"
            r"(?!\w)"
        ),
    ),
]


# ============================================================
# Environment
# ============================================================

def load_env_file() -> None:
    """
    Load values from the project-root .env file.

    Existing environment variables take precedence.
    """

    if not ENV_FILE.exists():
        return

    for line in ENV_FILE.read_text(
        encoding="utf-8"
    ).splitlines():

        line = line.strip()

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
    )

    if not token:
        raise RuntimeError(
            "GitHub token not found. "
            "Expected GITHUB_TOKEN in the project root .env file."
        )

    return token


# ============================================================
# GitHub client
# ============================================================

class GitHubNotFoundError(Exception):
    """GitHub resource does not exist or is no longer available."""


class GitHubGoneError(Exception):
    """GitHub resource is gone."""


class GitHubClient:

    def __init__(self, token: str):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ReleaseGuard-RealDataset/1.1.0",
            }
        )

    def get(
        self,
        url: str,
    ) -> requests.Response:

        response = self.session.get(
            url,
            timeout=TIMEOUT_SECONDS,
        )

        if response.status_code == 403:

            remaining = response.headers.get(
                "X-RateLimit-Remaining"
            )

            reset = response.headers.get(
                "X-RateLimit-Reset"
            )

            raise RuntimeError(
                "GitHub API rate limit/permission failure. "
                f"remaining={remaining}, reset={reset}"
            )

        if response.status_code == 404:
            raise GitHubNotFoundError(
                f"GitHub resource not found: {url}"
            )

        if response.status_code == 410:
            raise GitHubGoneError(
                f"GitHub resource is gone: {url}"
            )

        response.raise_for_status()

        time.sleep(API_DELAY_SECONDS)

        return response

    def get_issue(
        self,
        owner: str,
        repository: str,
        issue_number: int,
    ) -> dict[str, Any]:

        url = (
            f"{GITHUB_API}/repos/"
            f"{owner}/{repository}/issues/"
            f"{issue_number}"
        )

        return self.get(url).json()


# ============================================================
# Utility
# ============================================================

def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_json(path: Path) -> dict[str, Any]:

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def write_json(
    path: Path,
    data: dict[str, Any],
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
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )

        file.write("\n")

    temporary.replace(path)


# ============================================================
# PR discovery
# ============================================================

def discover_pr_files() -> list[Path]:

    if not PR_RAW_DIR.exists():

        raise FileNotFoundError(
            f"PR raw directory not found: {PR_RAW_DIR}"
        )

    return sorted(
        PR_RAW_DIR.rglob("pr-*.json")
    )


# ============================================================
# Issue reference extraction
# ============================================================

def extract_issue_references(
    text: str,
    default_owner: str,
    default_repo: str,
) -> list[dict[str, Any]]:
    """
    Extract GitHub issue references from PR text.

    Returns:

    [
        {
            "owner": "...",
            "repository": "...",
            "issue_number": 123,
            "reference_type": "local"
        }
    ]

    or:

    [
        {
            "owner": "...",
            "repository": "...",
            "issue_number": 123,
            "reference_type": "cross_repository"
        }
    ]
    """

    if not text:
        return []

    references: list[dict[str, Any]] = []

    seen: set[
        tuple[str, str, int]
    ] = set()

    for reference_type, pattern in ISSUE_REFERENCE_PATTERNS:

        for match in pattern.finditer(text):

            groups = match.groupdict()

            owner = (
                groups.get("owner")
                or default_owner
            )

            repository = (
                groups.get("repository")
                or default_repo
            )

            number_value = groups.get("number")

            if not number_value:
                continue

            issue_number = int(number_value)

            key = (
                owner.lower(),
                repository.lower(),
                issue_number,
            )

            if key in seen:
                continue

            seen.add(key)

            references.append(
                {
                    "owner": owner,
                    "repository": repository,
                    "issue_number": issue_number,
                    "reference_type": reference_type,
                }
            )

    return references


def extract_text_from_pr(
    pr: dict[str, Any],
) -> str:
    """
    Combine PR fields that may contain issue references.
    """

    pull_request = pr.get(
        "pull_request",
        {},
    )

    parts: list[str] = []

    for field in (
        "title",
        "body",
    ):

        value = pull_request.get(field)

        if value:
            parts.append(str(value))

    return "\n".join(parts)


# ============================================================
# Issue normalization
# ============================================================

def normalize_issue(
    issue_data: dict[str, Any],
    owner: str,
    repository: str,
    issue_number: int,
    reference_type: str,
) -> dict[str, Any]:

    closed_by = (
        issue_data.get("closed_by")
        or {}
    )

    return {
        "owner": owner,
        "repository": repository,
        "issue_number": issue_number,
        "reference_type": reference_type,

        "id": issue_data.get("id"),

        "node_id": issue_data.get(
            "node_id"
        ),

        "url": issue_data.get(
            "html_url"
        ),

        "api_url": issue_data.get(
            "url"
        ),

        "title": issue_data.get(
            "title"
        ),

        "body": issue_data.get(
            "body"
        ),

        "state": issue_data.get(
            "state"
        ),

        "state_reason": issue_data.get(
            "state_reason"
        ),

        "created_at": issue_data.get(
            "created_at"
        ),

        "updated_at": issue_data.get(
            "updated_at"
        ),

        "closed_at": issue_data.get(
            "closed_at"
        ),

        "closed_by": closed_by.get(
            "login"
        ),

        "labels": [
            label.get("name")
            for label in (
                issue_data.get("labels")
                or []
            )
        ],

        "comments": issue_data.get(
            "comments",
            0,
        ),

        "pull_request": issue_data.get(
            "pull_request"
        ),
    }


# ============================================================
# Main collection
# ============================================================

def main() -> None:

    started_at = utc_now()

    ISSUE_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    token = get_github_token()

    client = GitHubClient(token)

    pr_files = discover_pr_files()

    print("=" * 70)
    print("ReleaseGuard — Linked Issue Collection")
    print("=" * 70)

    print(
        f"PR records discovered: {len(pr_files)}"
    )

    print(
        f"Output directory: {ISSUE_RAW_DIR}"
    )

    print()

    processed_prs = 0
    prs_with_issue_references = 0

    issues_collected = 0
    skipped_existing = 0

    unresolved_references = 0

    errors: list[dict[str, Any]] = []

    issue_cache: dict[
        tuple[str, str, int],
        dict[str, Any] | None,
    ] = {}

    for index, pr_file in enumerate(
        pr_files,
        start=1,
    ):

        try:

            pr = load_json(pr_file)

            pull_request = pr.get(
                "pull_request",
                {},
            )

            repository = pr.get(
                "repository",
                {},
            )

            full_name = repository.get(
                "full_name"
            )

            pr_number = pull_request.get(
                "number"
            )

            if not full_name or not pr_number:
                continue

            processed_prs += 1

            pr_owner, pr_repo = (
                full_name.split(
                    "/",
                    1,
                )
            )

            text = extract_text_from_pr(pr)

            references = extract_issue_references(
                text=text,
                default_owner=pr_owner,
                default_repo=pr_repo,
            )

            if not references:
                continue

            prs_with_issue_references += 1

            collected_issues: list[
                dict[str, Any]
            ] = []

            unresolved_issues: list[
                dict[str, Any]
            ] = []

            for reference in references:

                owner = reference[
                    "owner"
                ]

                repo = reference[
                    "repository"
                ]

                issue_number = reference[
                    "issue_number"
                ]

                reference_type = reference[
                    "reference_type"
                ]

                cache_key = (
                    owner.lower(),
                    repo.lower(),
                    issue_number,
                )

                try:

                    if cache_key in issue_cache:

                        issue_data = issue_cache[
                            cache_key
                        ]

                        if issue_data is None:

                            unresolved_issues.append(
                                {
                                    **reference,
                                    "status": (
                                        "unresolved"
                                    ),
                                    "reason": (
                                        "cached_unresolved"
                                    ),
                                }
                            )

                            unresolved_references += 1

                            continue

                    else:

                        try:

                            issue_data = (
                                client.get_issue(
                                    owner,
                                    repo,
                                    issue_number,
                                )
                            )

                            issue_cache[
                                cache_key
                            ] = issue_data

                        except (
                            GitHubNotFoundError,
                            GitHubGoneError,
                        ) as exc:

                            issue_cache[
                                cache_key
                            ] = None

                            unresolved_issues.append(
                                {
                                    **reference,
                                    "status": (
                                        "unresolved"
                                    ),
                                    "reason": (
                                        str(exc)
                                    ),
                                }
                            )

                            unresolved_references += 1

                            continue

                    issue = normalize_issue(
                        issue_data=issue_data,
                        owner=owner,
                        repository=repo,
                        issue_number=issue_number,
                        reference_type=reference_type,
                    )

                    collected_issues.append(
                        issue
                    )

                    issues_collected += 1

                except Exception as exc:

                    errors.append(
                        {
                            "pr_file": str(
                                pr_file
                            ),
                            "repository": (
                                full_name
                            ),
                            "pull_request_number": (
                                pr_number
                            ),
                            "issue": (
                                f"{owner}/"
                                f"{repo}#"
                                f"{issue_number}"
                            ),
                            "error": str(exc),
                        }
                    )

            output = {
                "schema_version": SCHEMA_VERSION,
                "dataset_type": (
                    "releaseguard-real-linked-issues"
                ),
                "dataset_version": DATASET_VERSION,

                "collected_at": utc_now(),

                "pull_request": {
                    "repository": full_name,

                    "owner": pr_owner,

                    "name": pr_repo,

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
                },

                "linked_issues": (
                    collected_issues
                ),

                "unresolved_references": (
                    unresolved_issues
                ),
            }

            output_dir = (
                ISSUE_RAW_DIR
                / pr_owner
                / pr_repo
            )

            output_file = (
                output_dir
                / f"pr-{pr_number}.json"
            )

            if output_file.exists():

                skipped_existing += 1

            else:

                write_json(
                    output_file,
                    output,
                )

            if index % 25 == 0:

                print(
                    f"[{index}/{len(pr_files)}] "
                    f"PRs processed | "
                    f"Issue references: "
                    f"{prs_with_issue_references} | "
                    f"Issues collected: "
                    f"{issues_collected} | "
                    f"Unresolved: "
                    f"{unresolved_references}"
                )

        except Exception as exc:

            errors.append(
                {
                    "pr_file": str(
                        pr_file
                    ),
                    "error": str(exc),
                }
            )

    completed_at = utc_now()

    manifest = {
        "schema_version": SCHEMA_VERSION,

        "dataset_type": (
            "releaseguard-real-linked-issues"
        ),

        "dataset_version": DATASET_VERSION,

        "collection": {
            "access_method": (
                "GitHub REST API"
            ),

            "collector_version": (
                COLLECTOR_VERSION
            ),

            "started_at": started_at,

            "finished_at": completed_at,

            "http_method": "GET",

            "source_pr_records": len(
                pr_files
            ),

            "processed_pr_records": (
                processed_prs
            ),

            "prs_with_issue_references": (
                prs_with_issue_references
            ),

            "issues_collected": (
                issues_collected
            ),

            "unresolved_references": (
                unresolved_references
            ),

            "skipped_existing": (
                skipped_existing
            ),

            "total_errors": len(
                errors
            ),
        },

        "reference_resolution": {
            "resolved_issue_records": (
                issues_collected
            ),

            "unresolved_issue_references": (
                unresolved_references
            ),

            "unresolved_references_are_not_treated_as_collection_failures": (
                True
            ),
        },

        "storage": {
            "raw_directory": str(
                ISSUE_RAW_DIR
            )
        },

        "errors": errors,
    }

    write_json(
        COLLECTION_MANIFEST_FILE,
        manifest,
    )

    print()

    print("=" * 70)
    print("LINKED ISSUE COLLECTION COMPLETE")
    print("=" * 70)

    print(
        f"PR records processed: "
        f"{processed_prs}"
    )

    print(
        f"PRs with issue references: "
        f"{prs_with_issue_references}"
    )

    print(
        f"Issues collected: "
        f"{issues_collected}"
    )

    print(
        f"Unresolved references: "
        f"{unresolved_references}"
    )

    print(
        f"Errors: "
        f"{len(errors)}"
    )

    print()

    print(
        "Raw linked issues:"
        f"\n  {ISSUE_RAW_DIR}"
    )

    print()

    print(
        "Collection manifest:"
        f"\n  {COLLECTION_MANIFEST_FILE}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()