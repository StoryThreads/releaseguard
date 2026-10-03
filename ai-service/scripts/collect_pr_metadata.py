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

REPOSITORY_MANIFEST = MANIFEST_FILE

REPOSITORIES_FILE = (
    RAW_DIR / "repositories.jsonl"
)

PULL_REQUESTS_FILE = (
    RAW_DIR / "pull_requests.jsonl"
)

CHANGED_FILES_FILE = (
    RAW_DIR / "changed_files.jsonl"
)


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = os.getenv(
    "GITHUB_API_URL",
    "https://api.github.com",
)

API_VERSION = "2022-11-28"

PER_PAGE = 100

REQUEST_DELAY_SECONDS = 0.2

# Safety limit:
# avoid accidentally collecting enormous repositories.
MAX_PRS_PER_REPOSITORY = 500

# Only collect merged PRs for the initial ML dataset.
ONLY_MERGED_PRS = True


# ============================================================
# ENVIRONMENT
# ============================================================

def load_environment() -> None:
    """
    Load the root project's .env file.

    Expected:

        GITHUB_TOKEN=...
        GITHUB_API_URL=https://api.github.com
    """

    project_root = SCRIPT_DIR.parents[3]

    env_file = project_root / ".env"

    if env_file.exists():
        load_dotenv(env_file)

    load_dotenv()


# ============================================================
# HTTP CLIENT
# ============================================================

class GitHubClient:

    def __init__(self, token: str):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "ReleaseGuard-Real-Data-Collector",
            }
        )

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:

        url = f"{API_URL.rstrip('/')}{path}"

        while True:

            response = self.session.get(
                url,
                params=params,
                timeout=60,
            )

            if response.status_code == 403:
                remaining = response.headers.get(
                    "X-RateLimit-Remaining"
                )

                reset = response.headers.get(
                    "X-RateLimit-Reset"
                )

                if remaining == "0" and reset:

                    reset_time = int(reset)

                    wait_seconds = max(
                        reset_time
                        - int(time.time())
                        + 5,
                        5,
                    )

                    print(
                        f"Rate limit reached. "
                        f"Waiting {wait_seconds}s..."
                    )

                    time.sleep(wait_seconds)

                    continue

            if response.status_code == 429:

                retry_after = int(
                    response.headers.get(
                        "Retry-After",
                        "10",
                    )
                )

                print(
                    f"GitHub requested retry. "
                    f"Waiting {retry_after}s..."
                )

                time.sleep(retry_after)

                continue

            if not response.ok:

                raise RuntimeError(
                    f"GitHub API request failed: "
                    f"{response.status_code} "
                    f"{response.text}"
                )

            return response.json()


# ============================================================
# UTILITIES
# ============================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(
    path: Path,
    record: dict[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "a",
        encoding="utf-8",
    ) as file:

        file.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


def load_repositories() -> list[dict[str, str]]:

    if not REPOSITORY_MANIFEST.exists():

        raise FileNotFoundError(
            f"Repository manifest not found: "
            f"{REPOSITORY_MANIFEST}"
        )

    with REPOSITORY_MANIFEST.open(
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)

    # Your repositories.json contains an object:
    #
    # {
    #   "dataset_version": "...",
    #   "selection_policy_version": "...",
    #   "collection_scope": {...},
    #   "repositories": [...]
    # }
    #
    # Therefore we must extract the repositories array.

    if not isinstance(data, dict):

        raise ValueError(
            "repositories.json must contain an object."
        )

    repositories = data.get(
        "repositories"
    )

    if not isinstance(repositories, list):

        raise ValueError(
            "repositories.json must contain "
            "a 'repositories' array."
        )

    for repository in repositories:

        if not isinstance(repository, dict):

            raise ValueError(
                "Each repository entry must be an object."
            )

        if not repository.get("owner"):

            raise ValueError(
                "Repository entry missing owner."
            )

        if not repository.get("name"):

            raise ValueError(
                "Repository entry missing name."
            )

    return repositories

# ============================================================
# PAGINATION
# ============================================================

def get_all_pages(
    client: GitHubClient,
    path: str,
    params: dict[str, Any],
    max_items: int | None = None,
) -> list[Any]:

    results: list[Any] = []

    page = 1

    while True:

        request_params = dict(params)

        request_params["page"] = page
        request_params["per_page"] = PER_PAGE

        data = client.get(
            path,
            request_params,
        )

        if not isinstance(data, list):
            raise RuntimeError(
                f"Expected list response from {path}"
            )

        results.extend(data)

        if max_items is not None:
            if len(results) >= max_items:
                return results[:max_items]

        if len(data) < PER_PAGE:
            break

        page += 1

        time.sleep(
            REQUEST_DELAY_SECONDS
        )

    return results


# ============================================================
# REPOSITORY
# ============================================================

def collect_repository(
    client: GitHubClient,
    owner: str,
    repository: str,
) -> None:

    print()
    print(
        f"=================================================="
    )
    print(
        f"Collecting {owner}/{repository}"
    )
    print(
        f"=================================================="
    )

    repository_data = client.get(
        f"/repos/{owner}/{repository}"
    )

    repository_record = {
        "owner": owner,
        "name": repository,
        "full_name": repository_data.get(
            "full_name"
        ),
        "html_url": repository_data.get(
            "html_url"
        ),
        "clone_url": repository_data.get(
            "clone_url"
        ),
        "default_branch": repository_data.get(
            "default_branch"
        ),
        "language": repository_data.get(
            "language"
        ),
        "languages_url": repository_data.get(
            "languages_url"
        ),
        "license": (
            repository_data.get("license") or {}
        ).get("spdx_id"),
        "license_name": (
            repository_data.get("license") or {}
        ).get("name"),
        "fork": repository_data.get(
            "fork"
        ),
        "archived": repository_data.get(
            "archived"
        ),
        "has_issues": repository_data.get(
            "has_issues"
        ),
        "created_at": repository_data.get(
            "created_at"
        ),
        "updated_at": repository_data.get(
            "updated_at"
        ),
        "pushed_at": repository_data.get(
            "pushed_at"
        ),
        "stargazers_count": repository_data.get(
            "stargazers_count"
        ),
        "forks_count": repository_data.get(
            "forks_count"
        ),
        "open_issues_count": repository_data.get(
            "open_issues_count"
        ),
        "collection_timestamp": utc_now(),
    }

    append_jsonl(
        REPOSITORIES_FILE,
        repository_record,
    )

    print(
        f"License: "
        f"{repository_record['license']}"
    )

    # --------------------------------------------------------
    # Pull requests
    # --------------------------------------------------------

    pull_requests = get_all_pages(
        client,
        f"/repos/{owner}/{repository}/pulls",
        {
            "state": "closed",
            "sort": "created",
            "direction": "asc",
        },
        max_items=MAX_PRS_PER_REPOSITORY,
    )

    print(
        f"Closed PRs fetched: "
        f"{len(pull_requests)}"
    )

    merged_count = 0

    for pr in pull_requests:

        merged_at = pr.get("merged_at")

        if ONLY_MERGED_PRS and not merged_at:
            continue

        merged_count += 1

        pr_number = pr["number"]

        print(
            f"  PR #{pr_number}: "
            f"{pr.get('title', '')[:80]}"
        )

        # ----------------------------------------------------
        # PR metadata
        # ----------------------------------------------------

        user = pr.get("user") or {}

        base = pr.get("base") or {}
        head = pr.get("head") or {}

        repository_record_for_pr = {
            "repository": f"{owner}/{repository}",
            "repository_url": repository_data.get(
                "html_url"
            ),
            "repository_license": (
                repository_data.get("license") or {}
            ).get("spdx_id"),
        }

        pr_record = {
            **repository_record_for_pr,

            "pr_number": pr_number,

            "pr_url": pr.get(
                "html_url"
            ),

            "title": pr.get(
                "title"
            ),

            "body": pr.get(
                "body"
            ),

            "state": pr.get(
                "state"
            ),

            "draft": pr.get(
                "draft"
            ),

            "author": user.get(
                "login"
            ),

            "author_type": user.get(
                "type"
            ),

            "created_at": pr.get(
                "created_at"
            ),

            "updated_at": pr.get(
                "updated_at"
            ),

            "closed_at": pr.get(
                "closed_at"
            ),

            "merged_at": merged_at,

            "merge_commit_sha": pr.get(
                "merge_commit_sha"
            ),

            "base_branch": base.get(
                "ref"
            ),

            "base_sha": base.get(
                "sha"
            ),

            "head_branch": head.get(
                "ref"
            ),

            "head_sha": head.get(
                "sha"
            ),

            "labels": [
                label.get("name")
                for label in pr.get(
                    "labels",
                    []
                )
            ],

            "milestone": (
                pr.get("milestone") or {}
            ).get("title"),

            "locked": pr.get(
                "locked"
            ),

            "commits_count": pr.get(
                "commits"
            ),

            "changed_files_count": pr.get(
                "changed_files"
            ),

            "additions": pr.get(
                "additions"
            ),

            "deletions": pr.get(
                "deletions"
            ),

            "changed_files": pr.get(
                "changed_files"
            ),

            "review_comments_count": pr.get(
                "review_comments"
            ),

            "issue_comments_count": pr.get(
                "comments"
            ),

            "maintainer_can_modify": pr.get(
                "maintainer_can_modify"
            ),

            "collection_timestamp": utc_now(),
        }

        append_jsonl(
            PULL_REQUESTS_FILE,
            pr_record,
        )

        # ----------------------------------------------------
        # Changed files
        # ----------------------------------------------------

        files = get_all_pages(
            client,
            f"/repos/{owner}/{repository}"
            f"/pulls/{pr_number}/files",
            {},
        )

        for file_data in files:

            file_record = {
                "repository": (
                    f"{owner}/{repository}"
                ),

                "pr_number": pr_number,

                "filename": file_data.get(
                    "filename"
                ),

                "status": file_data.get(
                    "status"
                ),

                "additions": file_data.get(
                    "additions"
                ),

                "deletions": file_data.get(
                    "deletions"
                ),

                "changes": file_data.get(
                    "changes"
                ),

                "blob_url": file_data.get(
                    "blob_url"
                ),

                "raw_url": file_data.get(
                    "raw_url"
                ),

                "contents_url": file_data.get(
                    "contents_url"
                ),

                # Patch is the important raw signal
                # for our later ChangeSnapshot creation.
                "patch": file_data.get(
                    "patch"
                ),

                "collection_timestamp": utc_now(),
            }

            append_jsonl(
                CHANGED_FILES_FILE,
                file_record,
            )

        time.sleep(
            REQUEST_DELAY_SECONDS
        )

    print(
        f"Merged PRs collected: "
        f"{merged_count}"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    load_environment()

    token = os.getenv(
        "GITHUB_TOKEN"
    )

    if not token:

        raise RuntimeError(
            "GITHUB_TOKEN is not configured. "
            "Set it in the project's root .env."
        )

    repositories = load_repositories()

    print(
        f"Repositories selected: "
        f"{len(repositories)}"
    )

    print(
        f"Output directory: "
        f"{RAW_DIR}"
    )

    client = GitHubClient(
        token
    )

    for repository in repositories:

        owner = repository["owner"]
        name = repository["name"]

        try:

            collect_repository(
                client,
                owner,
                name,
            )

        except Exception as exc:

            print(
                f"ERROR collecting "
                f"{owner}/{name}: {exc}",
                file=sys.stderr,
            )

            # Continue with remaining repositories.
            continue

    print()
    print(
        "=================================================="
    )
    print(
        "Collection completed."
    )
    print(
        "=================================================="
    )


if __name__ == "__main__":
    main()