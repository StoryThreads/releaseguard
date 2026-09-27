from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ChangedFileInput:
    filename: str
    status: str
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: Optional[str] = None


@dataclass(frozen=True)
class ChangeSnapshotInput:
    pull_request_number: Optional[int]
    owner: Optional[str]
    repository: Optional[str]
    title: Optional[str]
    source_branch: Optional[str]
    target_branch: Optional[str]
    head_sha: Optional[str]

    changed_files: List[ChangedFileInput] = field(
        default_factory=list
    )

    total_additions: int = 0
    total_deletions: int = 0
    total_changes: int = 0


@dataclass(frozen=True)
class FindingInput:
    analyzer_type: str
    finding_type: str
    severity: str
    rule_id: Optional[str] = None
    title: Optional[str] = None
    message: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass(frozen=True)
class RiskAnalysisInput:
    change_snapshot: ChangeSnapshotInput
    findings: List[FindingInput] = field(
        default_factory=list
    )