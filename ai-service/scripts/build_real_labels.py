from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# PATHS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent

DATA_DIR = AI_SERVICE_DIR / "data" / "real"
RAW_DIR = DATA_DIR / "raw"
DEFECT_RAW_DIR = RAW_DIR / "post_merge_defect_signals"

MANIFEST_DIR = DATA_DIR / "manifests"

OUTPUT_DIR = DATA_DIR / "labeled"
OUTPUT_FILE = OUTPUT_DIR / "real_outcome_labels.jsonl"
LABEL_MANIFEST_FILE = (
    MANIFEST_DIR / "real_outcome_label_manifest.json"
)

LABEL_STRATEGY_VERSION = "1.0.0"
DATASET_VERSION = "1.0.0-real"
SCHEMA_VERSION = "1.0.0"


# ============================================================
# LABEL POLICY
# ============================================================

LABEL_ORDER = [
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]

LABEL_DEFINITIONS = {
    "LOW": {
        "ordinal": 0,
        "description": (
            "No observable post-merge defect evidence was "
            "collected for the pull request."
        ),
    },
    "MEDIUM": {
        "ordinal": 1,
        "description": (
            "Weak post-merge defect-oriented evidence was "
            "observed, such as a referenced issue containing "
            "fix/bug/regression-oriented wording without a "
            "recognized defect label."
        ),
    },
    "HIGH": {
        "ordinal": 2,
        "description": (
            "Moderate post-merge defect evidence was observed, "
            "such as a later follow-up pull request explicitly "
            "referencing the original pull request and "
            "containing defect/fix-oriented evidence."
        ),
    },
    "CRITICAL": {
        "ordinal": 3,
        "description": (
            "Strong post-merge defect evidence was observed, "
            "such as an explicit revert commit or a "
            "post-merge issue carrying recognized "
            "defect-oriented labels."
        ),
    },
}


# ============================================================
# OUTCOME LIMITATIONS
# ============================================================

LABEL_LIMITATIONS = [
    (
        "These labels represent observable post-merge defect "
        "evidence strength, not actual business or production "
        "impact severity."
    ),
    (
        "LOW means no qualifying signal was observed in the "
        "collected GitHub evidence; it does not prove that "
        "the change was defect-free."
    ),
    (
        "GitHub metadata cannot reliably establish customer "
        "impact, outage duration, financial impact, security "
        "impact, or production blast radius."
    ),
    (
        "Missing, inaccessible, deleted, or unreferenced "
        "post-merge evidence can cause false LOW outcomes."
    ),
    (
        "Only qualifying observable signals are used. "
        "Unrecognized wording is not interpreted as a defect."
    ),
    (
        "The current dataset may be strongly class-imbalanced "
        "because explicit post-merge defect evidence is rare."
    ),
]


# ============================================================
# HELPERS
# ============================================================

def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_json(path: Path) -> Any:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def write_json(
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

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        file.write("\n")

    temporary_path.replace(path)


def discover_signal_files() -> list[Path]:
    if not DEFECT_RAW_DIR.exists():
        raise FileNotFoundError(
            f"Post-merge defect signal directory not found: "
            f"{DEFECT_RAW_DIR}"
        )

    files = sorted(
        DEFECT_RAW_DIR.rglob("pr-*.json")
    )

    if not files:
        raise FileNotFoundError(
            f"No post-merge defect signal records found under: "
            f"{DEFECT_RAW_DIR}"
        )

    return files


# ============================================================
# SIGNAL CLASSIFICATION
# ============================================================

def signal_strength_rank(
    signal: dict[str, Any],
) -> int:
    strength = (
        signal.get("strength") or ""
    ).strip().lower()

    return {
        "weak": 1,
        "moderate": 2,
        "strong": 3,
    }.get(
        strength,
        0,
    )


def determine_outcome_label(
    record: dict[str, Any],
) -> tuple[str, str]:
    signals = record.get(
        "signals",
        [],
    )

    if not isinstance(signals, list):
        signals = []

    valid_signals = [
        signal
        for signal in signals
        if isinstance(signal, dict)
    ]

    pull_request = record.get("pull_request", {})
    pr_title = (pull_request.get("title") or "").strip().lower()
    is_revert_pr = (
        pr_title.startswith("revert ")
        or pr_title.startswith("revert:")
        or pr_title.startswith("reverted ")
        or "revert" in pr_title.split()
    )

    if not valid_signals and not is_revert_pr:
        return (
            "LOW",
            "No qualifying post-merge defect signal was observed.",
        )

    # 1. CRITICAL: A change that caused a severe post-merge defect requiring an explicit revert commit or defect issue
    has_post_revert = any(
        s.get("signal_type") in ("explicit_revert_commit", "post_merge_defect_issue")
        for s in valid_signals
    )
    if not is_revert_pr and has_post_revert:
        return (
            "CRITICAL",
            (
                "This change caused a post-merge defect requiring an "
                "explicit revert or post-merge defect issue."
            ),
        )

    # 2. HIGH: Revert / rollback pull requests or moderate defect follow-up PRs
    has_high_signal = any(
        s.get("signal_type") in ("revert_pull_request", "post_merge_followup_pr")
        or s.get("strength") == "moderate"
        for s in valid_signals
    )
    if is_revert_pr or has_high_signal:
        return (
            "HIGH",
            (
                "Change is an explicit revert/rollback PR or has "
                "moderate defect follow-up evidence."
            ),
        )

    # 3. MEDIUM: Post-merge defect discussions / regressions
    has_medium_signal = any(
        s.get("signal_type") == "post_merge_defect_discussion"
        or s.get("strength") == "weak"
        for s in valid_signals
    )
    if has_medium_signal:
        return (
            "MEDIUM",
            (
                "Post-merge discussion reports a regression or defect "
                "behavior caused by this change."
            ),
        )

    return (
        "LOW",
        "Signals were present but none had a recognized defect-evidence strength.",
    )



# ============================================================
# DATA QUALITY
# ============================================================

def determine_data_quality(
    record: dict[str, Any],
) -> dict[str, Any]:
    pull_request = record.get(
        "pull_request",
        {},
    )

    signals = record.get(
        "signals",
        [],
    )

    if not isinstance(
        pull_request,
        dict,
    ):
        pull_request = {}

    if not isinstance(
        signals,
        list,
    ):
        signals = []

    merged_at = pull_request.get(
        "merged_at"
    )

    signal_summary = record.get(
        "signal_summary",
        {},
    )

    if not isinstance(
        signal_summary,
        dict,
    ):
        signal_summary = {}

    missing_fields = []

    if not pull_request.get("repository"):
        missing_fields.append(
            "pull_request.repository"
        )

    if pull_request.get("number") is None:
        missing_fields.append(
            "pull_request.number"
        )

    if not merged_at:
        missing_fields.append(
            "pull_request.merged_at"
        )

    if missing_fields:
        return {
            "status": "INSUFFICIENT_DATA",
            "missing_fields": missing_fields,
            "reason": (
                "Required PR metadata needed to interpret "
                "post-merge outcome is missing."
            ),
        }

    return {
        "status": "OBSERVABLE",
        "missing_fields": [],
        "reason": (
            "Required PR metadata was available and the "
            "post-merge signal record was collected."
        ),
        "signal_count": len(signals),
        "has_any_signal": bool(
            signal_summary.get(
                "has_any_signal",
                bool(signals),
            )
        ),
    }


# ============================================================
# BUILD LABEL RECORD
# ============================================================

def build_label_record(
    signal_file: Path,
    record: dict[str, Any],
) -> dict[str, Any]:
    pull_request = record.get(
        "pull_request",
        {},
    )

    if not isinstance(
        pull_request,
        dict,
    ):
        pull_request = {}

    label, reason = determine_outcome_label(
        record
    )

    data_quality = determine_data_quality(
        record
    )

    signals = record.get(
        "signals",
        [],
    )

    if not isinstance(
        signals,
        list,
    ):
        signals = []

    signal_types = sorted(
        {
            signal.get("signal_type")
            for signal in signals
            if isinstance(signal, dict)
            and signal.get("signal_type")
        }
    )

    signal_strengths = sorted(
        {
            signal.get("strength")
            for signal in signals
            if isinstance(signal, dict)
            and signal.get("strength")
        }
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "label_strategy_version": LABEL_STRATEGY_VERSION,
        "dataset_version": DATASET_VERSION,
        "created_at": utc_now(),

        "source": {
            "signal_file": str(signal_file),
            "dataset_type": record.get(
                "dataset_type"
            ),
        },

        "pull_request": {
            "repository": pull_request.get(
                "repository"
            ),
            "owner": pull_request.get(
                "owner"
            ),
            "name": pull_request.get(
                "name"
            ),
            "number": pull_request.get(
                "number"
            ),
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
            "merged_at": pull_request.get(
                "merged_at"
            ),
            "merge_commit_sha": pull_request.get(
                "merge_commit_sha"
            ),
        },

        "outcome": {
            "label": label,
            "ordinal": LABEL_DEFINITIONS[
                label
            ]["ordinal"],
            "reason": reason,
            "evidence_signal_types": signal_types,
            "evidence_strengths": signal_strengths,
        },

        "data_quality": data_quality,
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("=" * 70)
    print(
        "ReleaseGuard — Real-World Outcome Labeling"
    )
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    signal_files = discover_signal_files()

    print(
        f"Signal records discovered: "
        f"{len(signal_files)}"
    )

    label_counts = Counter()
    quality_counts = Counter()
    signal_type_counts = Counter()

    records_written = 0
    ambiguous_records = 0
    insufficient_records = 0

    temporary_output = OUTPUT_FILE.with_suffix(
        OUTPUT_FILE.suffix + ".tmp"
    )

    with temporary_output.open(
        "w",
        encoding="utf-8",
    ) as output:

        for index, signal_file in enumerate(
            signal_files,
            start=1,
        ):
            record = load_json(
                signal_file
            )

            label_record = build_label_record(
                signal_file,
                record,
            )

            output.write(
                json.dumps(
                    label_record,
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            output.write("\n")

            records_written += 1

            label = label_record[
                "outcome"
            ]["label"]

            label_counts[label] += 1

            quality_status = label_record[
                "data_quality"
            ]["status"]

            quality_counts[
                quality_status
            ] += 1

            if label == "LOW":
                signals = record.get(
                    "signals",
                    [],
                )

                if signals:
                    ambiguous_records += 1

            if (
                quality_status
                == "INSUFFICIENT_DATA"
            ):
                insufficient_records += 1

            for signal_type in label_record[
                "outcome"
            ]["evidence_signal_types"]:
                signal_type_counts[
                    signal_type
                ] += 1

            if (
                index == 1
                or index % 100 == 0
                or index == len(signal_files)
            ):
                print(
                    f"[{index}/{len(signal_files)}] "
                    f"Labeled {label}"
                )

    temporary_output.replace(
        OUTPUT_FILE
    )

    total = records_written

    distribution = {}

    for label in LABEL_ORDER:
        count = label_counts[label]

        percentage = (
            (count / total) * 100
            if total
            else 0.0
        )

        distribution[label] = {
            "count": count,
            "percentage": round(
                percentage,
                4,
            ),
        }

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "label_strategy_version": (
            LABEL_STRATEGY_VERSION
        ),
        "dataset_version": DATASET_VERSION,
        "created_at": utc_now(),

        "policy": {
            "label_basis": (
                "Observable post-merge defect "
                "evidence strength"
            ),
            "labels": LABEL_DEFINITIONS,
            "limitations": LABEL_LIMITATIONS,
        },

        "collection": {
            "input_directory": str(
                DEFECT_RAW_DIR
            ),
            "output_file": str(
                OUTPUT_FILE
            ),
            "records_discovered": len(
                signal_files
            ),
            "records_written": records_written,
        },

        "label_distribution": distribution,

        "data_quality": {
            "counts": dict(
                quality_counts
            ),
            "insufficient_records": (
                insufficient_records
            ),
            "ambiguous_records": (
                ambiguous_records
            ),
        },

        "evidence_signal_counts": dict(
            signal_type_counts
        ),

        "training_warning": (
            "The label distribution must be inspected "
            "before supervised training. If one or more "
            "classes have zero or very few samples, the "
            "four-class problem is not statistically "
            "supported by this dataset."
        ),

        "limitations": LABEL_LIMITATIONS,
    }

    write_json(
        LABEL_MANIFEST_FILE,
        manifest,
    )

    print()
    print("=" * 70)
    print(
        "REAL-WORLD OUTCOME LABELING COMPLETE"
    )
    print("=" * 70)

    print(
        f"Records labeled : {records_written}"
    )

    print()
    print("Label distribution:")

    for label in LABEL_ORDER:
        item = distribution[label]

        print(
            f"  {label:<8} "
            f"{item['count']:>5} "
            f"({item['percentage']:>7.2f}%)"
        )

    print()
    print("Data quality:")

    for status, count in sorted(
        quality_counts.items()
    ):
        print(
            f"  {status:<20} {count}"
        )

    print()
    print(
        f"Labeled dataset:"
    )
    print(
        f"  {OUTPUT_FILE}"
    )

    print()
    print(
        f"Label manifest:"
    )
    print(
        f"  {LABEL_MANIFEST_FILE}"
    )

    print()
    print(
        "IMPORTANT:"
    )
    print(
        "These labels represent observable "
        "post-merge defect evidence strength."
    )
    print(
        "They do NOT represent actual production "
        "business impact severity."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()