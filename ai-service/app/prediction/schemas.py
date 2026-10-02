from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChangedFileRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    filename: str
    status: str

    additions: int = Field(
        default=0,
        ge=0,
    )

    deletions: int = Field(
        default=0,
        ge=0,
    )

    changes: int = Field(
        default=0,
        ge=0,
    )

    patch: Optional[str] = None


class ChangeSnapshotRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    pull_request_number: Optional[int] = Field(
        default=None,
        alias="pullRequestNumber",
        ge=1,
    )

    owner: Optional[str] = None

    repository: Optional[str] = None

    title: Optional[str] = None

    source_branch: Optional[str] = Field(
        default=None,
        alias="sourceBranch",
    )

    target_branch: Optional[str] = Field(
        default=None,
        alias="targetBranch",
    )

    head_sha: Optional[str] = Field(
        default=None,
        alias="headSha",
    )

    changed_files: List[ChangedFileRequest] = Field(
        default_factory=list,
        alias="changedFiles",
    )

    total_additions: int = Field(
        default=0,
        alias="totalAdditions",
        ge=0,
    )

    total_deletions: int = Field(
        default=0,
        alias="totalDeletions",
        ge=0,
    )

    total_changes: int = Field(
        default=0,
        alias="totalChanges",
        ge=0,
    )


class FindingRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    analyzer_type: str = Field(
        alias="analyzerType",
    )

    finding_type: str = Field(
        alias="findingType",
    )

    severity: str

    rule_id: Optional[str] = Field(
        default=None,
        alias="ruleId",
    )

    title: Optional[str] = None

    message: Optional[str] = None

    file_path: Optional[str] = Field(
        default=None,
        alias="filePath",
    )

    line_number: Optional[int] = Field(
        default=None,
        alias="lineNumber",
        ge=1,
    )


class PredictionRequest(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    change_snapshot: ChangeSnapshotRequest = Field(
        alias="changeSnapshot",
    )

    findings: List[FindingRequest] = Field(
        default_factory=list,
    )


class PredictionResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    risk_level: str

    risk_score: float

    class_probabilities: Dict[str, float]

    feature_vector: Dict[str, float]

    model_name: str

    model_version: str

    feature_version: str

    dataset_version: str