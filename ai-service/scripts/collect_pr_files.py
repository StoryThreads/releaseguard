from __future__ import annotations

import json
import os
import time
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
FILES_RAW_DIR = RAW_DIR / "pull_request_files"

MANIFEST_DIR = DATA_DIR / "manifests"

FILES_COLLECTION_MANIFEST = (
    MANIFEST_DIR / "pr_files_collection_manifest.json"
)


# ============================================================
# CONFIGURATION
# ============================================================

API_BASE_URL = "https://api.github.com"

REQUEST_TIMEOUT = 30

# GitHub recommends respecting API limits.
REQUEST_DELAY_SECONDS = 0.15

# GitHub returns up to 100 files per PR request.
PER_PAGE = 100

MAX_RETRIES = 5


# ============================================================
# ENVIRONMENT
# ============================================================

def load_env_file() -> None:
    """
    Minimal .env loader.

    The project already keeps the GitHub token in the root .env.
    """

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
            and value[0] == '"'
            and value[-1] == '"'
        ):
            value = value[1:-1]

        elif (
            len(value) >= 2
            and value[0] == "'"
            and value[-1] == "'"
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


def get_github_token() -> str:
    load_env_file()

    token = (
        os.getenv("GITHUB_TOKEN")
        or os.getenv("GH_TOKEN")
        or os.getenv("RELEASEGUARD_GITHUB_TOKEN")
    )

    if not token:
        raise RuntimeError(
            "GitHub token not found. "
            "Set GITHUB_TOKEN in the project root .env file."
        )

    return token


# ============================================================
# HTTP CLIENT
# ============================================================

class GitHubClient:

    def __init__(self, token: str):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "Accept": (
                    "application/vnd.github+json"
                ),
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ReleaseGuard-RealDataCollector",
            }
        )

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> requests.Response:

        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):

            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )

                # ------------------------------------------------
                # Rate limiting
                # ------------------------------------------------

                if response.status_code == 403:

                    remaining = response.headers.get(
                        "X-RateLimit-Remaining"
                    )

                    if remaining == "0":

                        reset_timestamp = response.headers.get(
                            "X-RateLimit-Reset"
                        )

                        if reset_timestamp:
                            wait_seconds = max(
                                1,
                                int(reset_timestamp)
                                - int(time.time())
                                + 1,
                            )
                        else:
                            wait_seconds = 60

                        print(
                            f"Rate limit reached. "
                            f"Waiting {wait_seconds}s..."
                        )

                        time.sleep(wait_seconds)
                        continue

                # ------------------------------------------------
                # Retry transient failures
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
                        f"Retrying in "
                        f"{wait_seconds}s..."
                    )

                    time.sleep(wait_seconds)
                    continue

                response.raise_for_status()

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

    FILES_RAW_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def atomic_write_json(
    path: Path,
    data: Any,
) -> None:

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
# PR DISCOVERY
# ============================================================

def extract_pr_identity(
    payload: dict[str, Any],
) -> tuple[str, str, int] | None:

    owner = payload.get("owner")
    repository = payload.get("repository")

    number = (
        payload.get("number")
        or payload.get("pull_request_number")
    )

    # --------------------------------------------------------
    # Handle nested repository structures if present.
    # --------------------------------------------------------

    if not owner:

        repository_data = payload.get(
            "repository_data"
        )

        if isinstance(repository_data, dict):
            owner = repository_data.get("owner")

    if not repository:

        repository_data = payload.get(
            "repository_data"
        )

        if isinstance(repository_data, dict):
            repository = repository_data.get(
                "name"
            )

    if not owner or not repository or number is None:
        return None

    try:
        number = int(number)
    except (TypeError, ValueError):
        return None

    return (
        str(owner),
        str(repository),
        number,
    )


def discover_prs() -> list[tuple[str, str, int]]:
    """
    Read the already-collected raw PR records.

    We deliberately do not query GitHub for PR numbers again.
    This guarantees that changed-file collection operates on
    exactly the same PRs as the existing real-world dataset.
    """

    if not PR_RAW_DIR.exists():
        raise FileNotFoundError(
            f"PR raw directory not found: {PR_RAW_DIR}"
        )

    discovered: dict[
        tuple[str, str, int],
        Path,
    ] = {}

    json_files = sorted(
        PR_RAW_DIR.rglob("*.json")
    )

    if not json_files:
        raise FileNotFoundError(
            f"No PR JSON files found under: "
            f"{PR_RAW_DIR}"
        )

    for path in json_files:

        # Skip temporary files.
        if path.name.endswith(".tmp"):
            continue

        try:
            payload = load_json(path)

        except (OSError, json.JSONDecodeError) as exc:

            print(
                f"WARNING: Could not read {path}: {exc}"
            )

            continue

        # ----------------------------------------------------
        # Supported shapes:
        #
        # 1. Single PR object
        # 2. {"pull_requests": [...]}
        # 3. {"prs": [...]}
        # 4. {"data": [...]}
        # ----------------------------------------------------

        records: list[dict[str, Any]] = []

        if isinstance(payload, dict):

            if (
                "pull_requests" in payload
                and isinstance(
                    payload["pull_requests"],
                    list,
                )
            ):
                records = [
                    item
                    for item in payload["pull_requests"]
                    if isinstance(item, dict)
                ]

            elif (
                "prs" in payload
                and isinstance(
                    payload["prs"],
                    list,
                )
            ):
                records = [
                    item
                    for item in payload["prs"]
                    if isinstance(item, dict)
                ]

            elif (
                "data" in payload
                and isinstance(
                    payload["data"],
                    list,
                )
            ):
                records = [
                    item
                    for item in payload["data"]
                    if isinstance(item, dict)
                ]

            else:
                records = [payload]

        elif isinstance(payload, list):

            records = [
                item
                for item in payload
                if isinstance(item, dict)
            ]

        for record in records:

            identity = extract_pr_identity(record)

            if identity is None:
                continue

            discovered[identity] = path

    return sorted(
        discovered.keys(),
        key=lambda item: (
            item[0].lower(),
            item[1].lower(),
            item[2],
        ),
    )


# ============================================================
# OUTPUT PATH
# ============================================================

def output_path(
    owner: str,
    repository: str,
    pr_number: int,
) -> Path:

    repository_directory = (
        FILES_RAW_DIR
        / owner
        / repository
    )

    repository_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return (
        repository_directory
        / f"pr-{pr_number}.json"
    )


# ============================================================
# GITHUB API
# ============================================================

def fetch_pr_files(
    client: GitHubClient,
    owner: str,
    repository: str,
    pr_number: int,
) -> list[dict[str, Any]]:

    all_files: list[dict[str, Any]] = []

    page = 1

    while True:

        url = (
            f"{API_BASE_URL}"
            f"/repos/{owner}/{repository}"
            f"/pulls/{pr_number}/files"
        )

        response = client.get(
            url,
            params={
                "per_page": PER_PAGE,
                "page": page,
            },
        )

        data = response.json()

        if not isinstance(data, list):
            raise RuntimeError(
                "Unexpected GitHub response for "
                f"{owner}/{repository}#{pr_number}"
            )

        if not data:
            break

        all_files.extend(data)

        if len(data) < PER_PAGE:
            break

        page += 1

        time.sleep(
            REQUEST_DELAY_SECONDS
        )

    return all_files


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_file(
    file_data: dict[str, Any],
) -> dict[str, Any]:

    """
    Keep the information required for ReleaseGuard ML
    feature extraction while preserving the original GitHub
    patch when available.
    """

    return {
        "sha": file_data.get("sha"),
        "filename": file_data.get("filename"),
        "status": file_data.get("status"),
        "additions": file_data.get(
            "additions",
            0,
        ),
        "deletions": file_data.get(
            "deletions",
            0,
        ),
        "changes": file_data.get(
            "changes",
            0,
        ),
        "blob_url": file_data.get("blob_url"),
        "raw_url": file_data.get("raw_url"),
        "contents_url": file_data.get(
            "contents_url"
        ),
        "previous_filename": file_data.get(
            "previous_filename"
        ),
        "patch": file_data.get("patch"),
    }


def build_record(
    owner: str,
    repository: str,
    pr_number: int,
    files: list[dict[str, Any]],
) -> dict[str, Any]:

    normalized_files = [
        normalize_file(file_data)
        for file_data in files
    ]

    total_additions = sum(
        int(file_data.get("additions") or 0)
        for file_data in normalized_files
    )

    total_deletions = sum(
        int(file_data.get("deletions") or 0)
        for file_data in normalized_files
    )

    total_changes = sum(
        int(file_data.get("changes") or 0)
        for file_data in normalized_files
    )

    return {
        "dataset_version": "1.0.0-real",
        "collection_type": "pull_request_files",
        "repository": {
            "owner": owner,
            "name": repository,
            "full_name": f"{owner}/{repository}",
        },
        "pull_request": {
            "number": pr_number,
        },
        "statistics": {
            "changed_files": len(
                normalized_files
            ),
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_changes": total_changes,
        },
        "files": normalized_files,
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print("=" * 70)
    print("ReleaseGuard — Real GitHub PR File/Diff Collection")
    print("=" * 70)

    ensure_directories()

    token = get_github_token()

    client = GitHubClient(token)

    prs = discover_prs()

    print(
        f"PRs discovered from existing raw dataset: "
        f"{len(prs)}"
    )

    processed = 0
    skipped = 0
    errors = 0
    total_files = 0

    error_records: list[dict[str, Any]] = []

    started_at = time.time()

    for index, (
        owner,
        repository,
        pr_number,
    ) in enumerate(prs, start=1):

        destination = output_path(
            owner,
            repository,
            pr_number,
        )

        # ----------------------------------------------------
        # Resume support
        # ----------------------------------------------------

        if destination.exists():

            skipped += 1

            print(
                f"[{index}/{len(prs)}] "
                f"SKIP "
                f"{owner}/{repository}#{pr_number}"
            )

            try:
                existing = load_json(
                    destination
                )

                existing_files = existing.get(
                    "files",
                    [],
                )

                total_files += len(
                    existing_files
                )

            except Exception:
                pass

            continue

        print(
            f"[{index}/{len(prs)}] "
            f"Collecting "
            f"{owner}/{repository}#{pr_number}"
        )

        try:

            files = fetch_pr_files(
                client,
                owner,
                repository,
                pr_number,
            )

            record = build_record(
                owner,
                repository,
                pr_number,
                files,
            )

            atomic_write_json(
                destination,
                record,
            )

            processed += 1
            total_files += len(files)

            print(
                f"    files={len(files)} "
                f"additions="
                f"{record['statistics']['total_additions']} "
                f"deletions="
                f"{record['statistics']['total_deletions']}"
            )

        except Exception as exc:

            errors += 1

            error_record = {
                "owner": owner,
                "repository": repository,
                "pull_request_number": pr_number,
                "error": str(exc),
            }

            error_records.append(
                error_record
            )

            print(
                f"    ERROR: {exc}"
            )

        time.sleep(
            REQUEST_DELAY_SECONDS
        )

    # ========================================================
    # COLLECTION MANIFEST
    # ========================================================

    completed_at = time.time()

    manifest = {
        "dataset_version": "1.0.0-real",
        "collection_type": "pull_request_files",
        "source": "GitHub REST API",
        "scope": {
            "pr_count_discovered": len(prs),
            "processed": processed,
            "skipped_existing": skipped,
            "errors": errors,
            "total_files": total_files,
        },
        "api": {
            "endpoint": (
                "/repos/{owner}/{repo}/pulls/{pull_number}/files"
            ),
            "per_page": PER_PAGE,
        },
        "storage": {
            "raw_directory": str(
                FILES_RAW_DIR
            ),
        },
        "collection": {
            "started_at_unix": started_at,
            "completed_at_unix": completed_at,
            "duration_seconds": (
                completed_at - started_at
            ),
        },
        "errors": error_records,
    }

    atomic_write_json(
        FILES_COLLECTION_MANIFEST,
        manifest,
    )

    print()
    print("=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)
    print(
        f"PRs discovered: {len(prs)}"
    )
    print(
        f"New PRs processed: {processed}"
    )
    print(
        f"Already collected: {skipped}"
    )
    print(
        f"Total changed files: {total_files}"
    )
    print(
        f"Errors: {errors}"
    )
    print()
    print("Raw file/diff data:")
    print(
        f"  {FILES_RAW_DIR}"
    )
    print()
    print("Collection manifest:")
    print(
        f"  {FILES_COLLECTION_MANIFEST}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()