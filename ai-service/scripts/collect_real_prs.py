from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


# ============================================================
# PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = AI_SERVICE_DIR.parent

ENV_FILE = PROJECT_ROOT / ".env"

DATA_DIR = AI_SERVICE_DIR / "data" / "real"
RAW_DIR = DATA_DIR / "raw"

REPOSITORY_RAW_DIR = RAW_DIR / "repositories"
PR_RAW_DIR = RAW_DIR / "pull_requests"

MANIFEST_FILE = (
    DATA_DIR
    / "manifests"
    / "repositories.json"
)

COLLECTION_MANIFEST_FILE = (
    DATA_DIR
    / "manifests"
    / "pr_collection_manifest.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

GITHUB_API_BASE = "https://api.github.com"

PER_PAGE = 100

# Maximum merged PRs collected from each repository
MAX_PRS_PER_REPOSITORY = int(os.getenv("COLLECT_LIMIT", "100"))

REQUEST_TIMEOUT_SECONDS = 30

REQUEST_DELAY_SECONDS = 0.25

MAX_RETRIES = 5


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(ENV_FILE)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise RuntimeError(
        f"GITHUB_TOKEN was not found in {ENV_FILE}"
    )


# ============================================================
# HTTP CLIENT
# ============================================================

session = requests.Session()

session.headers.update(
    {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ReleaseGuard-RealDataCollector/1.0",
    }
)


# ============================================================
# HELPERS
# ============================================================

def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def ensure_directories() -> None:
    REPOSITORY_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    PR_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    COLLECTION_MANIFEST_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


def read_json(path: Path) -> Any:
    with path.open(
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def write_json(
    path: Path,
    data: Any
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
            sort_keys=True
        )

        file.write("\n")

    temporary_path.replace(path)


def github_request(
    method: str,
    url: str,
    **kwargs: Any
) -> requests.Response:

    if method.upper() != "GET":
        raise RuntimeError(
            "ReleaseGuard real-data collector is read-only. "
            "Only GET requests are permitted."
        )

    for attempt in range(MAX_RETRIES):

        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            **kwargs
        )

        # ----------------------------------------------------
        # Success
        # ----------------------------------------------------

        if response.status_code == 200:
            return response

        # ----------------------------------------------------
        # Rate limiting
        # ----------------------------------------------------

        if response.status_code in (403, 429):

            retry_after = response.headers.get(
                "Retry-After"
            )

            if retry_after:

                sleep_seconds = int(
                    retry_after
                )

            else:

                remaining = response.headers.get(
                    "X-RateLimit-Remaining"
                )

                reset = response.headers.get(
                    "X-RateLimit-Reset"
                )

                if remaining == "0" and reset:

                    reset_timestamp = int(reset)

                    sleep_seconds = max(
                        1,
                        reset_timestamp
                        - int(time.time())
                        + 1
                    )

                else:

                    sleep_seconds = min(
                        60,
                        2 ** attempt
                    )

            print(
                f"GitHub rate limit reached. "
                f"Sleeping {sleep_seconds}s..."
            )

            time.sleep(sleep_seconds)

            continue

        # ----------------------------------------------------
        # Temporary server errors
        # ----------------------------------------------------

        if response.status_code in (
            500,
            502,
            503,
            504
        ):

            sleep_seconds = min(
                60,
                2 ** attempt
            )

            print(
                f"GitHub temporary error "
                f"{response.status_code}. "
                f"Retrying in {sleep_seconds}s..."
            )

            time.sleep(sleep_seconds)

            continue

        # ----------------------------------------------------
        # Permanent failure
        # ----------------------------------------------------

        raise RuntimeError(
            f"GitHub GET failed: "
            f"{response.status_code} "
            f"{response.text[:1000]}"
        )

    raise RuntimeError(
        f"GitHub request failed after "
        f"{MAX_RETRIES} attempts: {url}"
    )


def get_json(
    url: str,
    **kwargs: Any
) -> Any:

    response = github_request(
        "GET",
        url,
        **kwargs
    )

    time.sleep(
        REQUEST_DELAY_SECONDS
    )

    return response.json()


def get_text(
    url: str,
    accept: str
) -> str:

    response = github_request(
        "GET",
        url,
        headers={
            "Accept": accept
        }
    )

    time.sleep(
        REQUEST_DELAY_SECONDS
    )

    return response.text


# ============================================================
# REPOSITORY
# ============================================================

def fetch_repository(
    owner: str,
    name: str
) -> dict[str, Any]:

    url = (
        f"{GITHUB_API_BASE}"
        f"/repos/{owner}/{name}"
    )

    repository = get_json(url)

    if repository.get("private") is True:

        raise RuntimeError(
            f"Repository is private: "
            f"{owner}/{name}"
        )

    if repository.get("fork") is True:

        raise RuntimeError(
            f"Repository is a fork: "
            f"{owner}/{name}"
        )

    if repository.get("archived") is True:

        raise RuntimeError(
            f"Repository is archived: "
            f"{owner}/{name}"
        )

    return repository


# ============================================================
# PULL REQUESTS
# ============================================================

def fetch_merged_pull_requests(
    owner: str,
    name: str,
    maximum: int
) -> list[dict[str, Any]]:

    collected: list[dict[str, Any]] = []

    page = 1

    while len(collected) < maximum:

        url = (
            f"{GITHUB_API_BASE}"
            f"/repos/{owner}/{name}/pulls"
        )

        per_page = min(
            PER_PAGE,
            maximum - len(collected)
        )

        params = {
            "state": "closed",
            "sort": "updated",
            "direction": "desc",
            "per_page": per_page,
            "page": page,
        }

        pull_requests = get_json(
            url,
            params=params
        )

        if not pull_requests:
            break

        for pull_request in pull_requests:

            if pull_request.get("merged_at"):

                collected.append(
                    pull_request
                )

                if len(collected) >= maximum:
                    break

        if len(pull_requests) < per_page:
            break

        page += 1

    return collected


def fetch_defect_and_revert_pull_requests(
    owner: str,
    name: str,
    maximum: int = 15
) -> list[dict[str, Any]]:
    """Targeted search for merged revert pull requests to guarantee post-merge defect representation."""
    url = f"{GITHUB_API_BASE}/search/issues"
    query = f"repo:{owner}/{name} is:pr is:merged revert in:title"
    params = {
        "q": query,
        "sort": "updated",
        "order": "desc",
        "per_page": min(maximum, 30),
    }
    try:
        data = get_json(url, params=params)
        items = data.get("items", [])
        return items[:maximum]
    except Exception as e:
        print(f"    Notice: Search for revert PRs in {owner}/{name} returned: {e}")
        return []


def fetch_pull_request(

    owner: str,
    name: str,
    number: int
) -> dict[str, Any]:

    url = (
        f"{GITHUB_API_BASE}"
        f"/repos/{owner}/{name}"
        f"/pulls/{number}"
    )

    return get_json(url)


def fetch_pull_request_files(
    owner: str,
    name: str,
    number: int
) -> list[dict[str, Any]]:

    url = (
        f"{GITHUB_API_BASE}"
        f"/repos/{owner}/{name}"
        f"/pulls/{number}/files"
    )

    files: list[dict[str, Any]] = []

    page = 1

    while True:

        response = get_json(
            url,
            params={
                "per_page": PER_PAGE,
                "page": page,
            }
        )

        if not response:
            break

        files.extend(response)

        if len(response) < PER_PAGE:
            break

        page += 1

    return files


def fetch_pull_request_diff(
    owner: str,
    name: str,
    number: int
) -> str:

    url = (
        f"{GITHUB_API_BASE}"
        f"/repos/{owner}/{name}"
        f"/pulls/{number}"
    )

    return get_text(
        url,
        "application/vnd.github.v3.diff"
    )


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_pull_request(
    repository: dict[str, Any],
    pull_request: dict[str, Any],
    files: list[dict[str, Any]],
    diff: str
) -> dict[str, Any]:

    return {
        "dataset_type": "releaseguard-real-pr",
        "schema_version": "1.0.0",

        "collected_at": utc_now(),

        "repository": {
            "id": repository.get("id"),
            "node_id": repository.get("node_id"),
            "full_name": repository.get("full_name"),
            "html_url": repository.get("html_url"),
            "default_branch": (
                repository
                .get("default_branch")
            ),
            "language": repository.get(
                "language"
            ),
            "license": (
                repository
                .get("license")
            ),
            "fork": repository.get("fork"),
            "archived": repository.get(
                "archived"
            ),
            "private": repository.get(
                "private"
            ),
        },

        "pull_request": {
            "id": pull_request.get("id"),
            "node_id": pull_request.get(
                "node_id"
            ),
            "number": pull_request.get(
                "number"
            ),
            "html_url": pull_request.get(
                "html_url"
            ),
            "title": pull_request.get(
                "title"
            ),
            "body": pull_request.get(
                "body"
            ),
            "state": pull_request.get(
                "state"
            ),
            "draft": pull_request.get(
                "draft"
            ),
            "created_at": pull_request.get(
                "created_at"
            ),
            "updated_at": pull_request.get(
                "updated_at"
            ),
            "closed_at": pull_request.get(
                "closed_at"
            ),
            "merged_at": pull_request.get(
                "merged_at"
            ),
            "merge_commit_sha": pull_request.get(
                "merge_commit_sha"
            ),
            "user": (
                pull_request
                .get("user", {})
                .get("login")
            ),
            "base": {
                "ref": (
                    pull_request
                    .get("base", {})
                    .get("ref")
                ),
                "sha": (
                    pull_request
                    .get("base", {})
                    .get("sha")
                ),
            },
            "head": {
                "ref": (
                    pull_request
                    .get("head", {})
                    .get("ref")
                ),
                "sha": (
                    pull_request
                    .get("head", {})
                    .get("sha")
                ),
            },
            "commits": pull_request.get(
                "commits"
            ),
            "additions": pull_request.get(
                "additions"
            ),
            "deletions": pull_request.get(
                "deletions"
            ),
            "changed_files": pull_request.get(
                "changed_files"
            ),
            "comments": pull_request.get(
                "comments"
            ),
            "review_comments": pull_request.get(
                "review_comments"
            ),
            "commits_url": pull_request.get(
                "commits_url"
            ),
            "comments_url": pull_request.get(
                "comments_url"
            ),
            "review_comments_url": pull_request.get(
                "review_comments_url"
            ),
            "issues_url": pull_request.get(
                "issue_url"
            ),
        },

        "files": [
            {
                "sha": file.get("sha"),
                "filename": file.get(
                    "filename"
                ),
                "status": file.get(
                    "status"
                ),
                "additions": file.get(
                    "additions"
                ),
                "deletions": file.get(
                    "deletions"
                ),
                "changes": file.get(
                    "changes"
                ),
                "blob_url": file.get(
                    "blob_url"
                ),
                "raw_url": file.get(
                    "raw_url"
                ),
                "contents_url": file.get(
                    "contents_url"
                ),
                "patch": file.get(
                    "patch"
                ),
            }
            for file in files
        ],

        "diff": diff,
    }


# ============================================================
# MAIN COLLECTION
# ============================================================

def collect() -> None:

    ensure_directories()

    manifest = read_json(
        MANIFEST_FILE
    )

    repositories = manifest.get(
        "repositories",
        []
    )

    if not repositories:

        raise RuntimeError(
            "No repositories found in "
            f"{MANIFEST_FILE}"
        )

    collection_started_at = utc_now()

    collection_results: list[
        dict[str, Any]
    ] = []

    print()
    print("=" * 70)
    print("ReleaseGuard Real GitHub PR Collector")
    print("=" * 70)
    print(
        f"Repositories: {len(repositories)}"
    )
    print(
        f"PR limit/repository: "
        f"{MAX_PRS_PER_REPOSITORY}"
    )
    print(
        "Mode: READ ONLY"
    )
    print("=" * 70)
    print()

    for repository_entry in repositories:

        owner = repository_entry["owner"]
        name = repository_entry["name"]

        full_name = f"{owner}/{name}"

        print(
            f"[Repository] {full_name}"
        )

        result = {
            "repository": full_name,
            "status": "started",
            "started_at": utc_now(),
            "pull_requests_collected": 0,
            "errors": [],
        }

        try:

            # ------------------------------------------------
            # Verify repository
            # ------------------------------------------------

            repository = fetch_repository(
                owner,
                name
            )

            repository_file = (
                REPOSITORY_RAW_DIR
                / f"{owner}__{name}.json"
            )

            repository_record = {
                "collected_at": utc_now(),
                "selection_manifest_entry": (
                    repository_entry
                ),
                "github_repository": repository,
            }

            write_json(
                repository_file,
                repository_record
            )

            print(
                f"  Repository verified"
            )

            # ------------------------------------------------
            # Get merged PRs
            # ------------------------------------------------

            pull_requests = (
                fetch_merged_pull_requests(
                    owner,
                    name,
                    MAX_PRS_PER_REPOSITORY
                )
            )

            # Targeted defect/revert PRs to guarantee HIGH and CRITICAL defect representation
            revert_prs = fetch_defect_and_revert_pull_requests(
                owner,
                name,
                maximum=15
            )
            existing_numbers = {pr.get("number") for pr in pull_requests}
            added_reverts = 0
            for r_pr in revert_prs:
                num = r_pr.get("number")
                if num and num not in existing_numbers:
                    pull_requests.append(r_pr)
                    existing_numbers.add(num)
                    added_reverts += 1

            print(
                f"  Merged PRs found: "
                f"{len(pull_requests)} (including {added_reverts} targeted revert/defect PRs)"
            )

            # ------------------------------------------------
            # Collect each PR
            # ------------------------------------------------

            for index, summary in enumerate(
                pull_requests,
                start=1
            ):

                number = summary.get(
                    "number"
                )

                pr_file = (
                    PR_RAW_DIR
                    / owner
                    / name
                    / f"pr-{number}.json"
                )

                if pr_file.exists():
                    print(
                        f"  [{index}/"
                        f"{len(pull_requests)}] "
                        f"PR #{number} (cached)"
                    )
                    result[
                        "pull_requests_collected"
                    ] += 1
                    continue

                print(
                    f"  [{index}/"
                    f"{len(pull_requests)}] "
                    f"PR #{number}"
                )


                try:

                    pull_request = (
                        fetch_pull_request(
                            owner,
                            name,
                            number
                        )
                    )

                    files = (
                        fetch_pull_request_files(
                            owner,
                            name,
                            number
                        )
                    )

                    diff = (
                        fetch_pull_request_diff(
                            owner,
                            name,
                            number
                        )
                    )

                    normalized = (
                        normalize_pull_request(
                            repository,
                            pull_request,
                            files,
                            diff
                        )
                    )

                    pr_file = (
                        PR_RAW_DIR
                        / owner
                        / name
                        / f"pr-{number}.json"
                    )

                    write_json(
                        pr_file,
                        normalized
                    )

                    result[
                        "pull_requests_collected"
                    ] += 1

                except Exception as exception:

                    error_message = (
                        f"PR #{number}: "
                        f"{type(exception).__name__}: "
                        f"{exception}"
                    )

                    print(
                        f"    ERROR: "
                        f"{error_message}"
                    )

                    result[
                        "errors"
                    ].append(
                        error_message
                    )

        except Exception as exception:

            error_message = (
                f"{type(exception).__name__}: "
                f"{exception}"
            )

            print(
                f"  ERROR: "
                f"{error_message}"
            )

            result["errors"].append(
                error_message
            )

        result["finished_at"] = utc_now()

        if result["errors"]:

            if result[
                "pull_requests_collected"
            ] > 0:

                result["status"] = (
                    "completed_with_errors"
                )

            else:

                result["status"] = "failed"

        else:

            result["status"] = "completed"

        collection_results.append(
            result
        )

        print()

    collection_finished_at = utc_now()

    # ========================================================
    # Collection manifest
    # ========================================================

    total_prs = sum(
        result[
            "pull_requests_collected"
        ]
        for result in collection_results
    )

    total_errors = sum(
        len(result["errors"])
        for result in collection_results
    )

    collection_manifest = {

        "dataset_type":
            "releaseguard-real-pr",

        "schema_version":
            "1.0.0",

        "dataset_version":
            manifest.get(
                "dataset_version",
                "1.0.0-real"
            ),

        "selection_policy_version":
            manifest.get(
                "selection_policy_version",
                "1.0.0"
            ),

        "collection": {

            "started_at":
                collection_started_at,

            "finished_at":
                collection_finished_at,

            "collector_version":
                "1.0.0",

            "access_method":
                "GitHub REST API",

            "http_method":
                "GET",

            "repository_count":
                len(repositories),

            "total_pull_requests":
                total_prs,

            "total_errors":
                total_errors,

            "max_pull_requests_per_repository":
                MAX_PRS_PER_REPOSITORY,
        },

        "repositories":
            collection_results,
    }

    write_json(
        COLLECTION_MANIFEST_FILE,
        collection_manifest
    )

    print("=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print(
        f"Repositories processed: "
        f"{len(repositories)}"
    )
    print(
        f"Pull requests collected: "
        f"{total_prs}"
    )
    print(
        f"Errors: "
        f"{total_errors}"
    )
    print()
    print(
        "Raw data:"
    )
    print(
        f"  {PR_RAW_DIR}"
    )
    print()
    print(
        "Collection manifest:"
    )
    print(
        f"  {COLLECTION_MANIFEST_FILE}"
    )
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        collect()

    except KeyboardInterrupt:

        print(
            "\nCollection interrupted by user."
        )

        sys.exit(130)

    except Exception as exception:

        print(
            "\nCollection failed:"
        )

        print(
            f"{type(exception).__name__}: "
            f"{exception}"
        )

        sys.exit(1)