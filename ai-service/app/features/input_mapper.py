from typing import Any, Dict, List

from app.features.input_schema import (
    ChangeSnapshotInput,
    ChangedFileInput,
    FindingInput,
    RiskAnalysisInput,
)


class InputMapper:
    """
    Maps the Java ReleaseGuard JSON contract into the
    internal Python V0.5 feature-engineering contract.
    """

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> RiskAnalysisInput:
        if not isinstance(data, dict):
            raise TypeError("Input must be a dictionary")

        change_snapshot_data = data.get("changeSnapshot", {})

        changed_files = [
            InputMapper._map_changed_file(file_data)
            for file_data in change_snapshot_data.get(
                "changedFiles",
                [],
            )
        ]

        change_snapshot = ChangeSnapshotInput(
            pull_request_number=change_snapshot_data.get(
                "pullRequestNumber"
            ),
            owner=change_snapshot_data.get("owner"),
            repository=change_snapshot_data.get("repository"),
            title=change_snapshot_data.get("title"),
            source_branch=change_snapshot_data.get("sourceBranch"),
            target_branch=change_snapshot_data.get("targetBranch"),
            head_sha=change_snapshot_data.get("headSha"),
            changed_files=changed_files,
            total_additions=change_snapshot_data.get(
                "totalAdditions",
                0,
            ),
            total_deletions=change_snapshot_data.get(
                "totalDeletions",
                0,
            ),
            total_changes=change_snapshot_data.get(
                "totalChanges",
                0,
            ),
        )

        findings = [
            InputMapper._map_finding(finding_data)
            for finding_data in data.get("findings", [])
        ]

        return RiskAnalysisInput(
            change_snapshot=change_snapshot,
            findings=findings,
        )

    @staticmethod
    def _map_changed_file(
        data: Dict[str, Any],
    ) -> ChangedFileInput:
        return ChangedFileInput(
            filename=data.get("filename", ""),
            status=data.get("status", ""),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            changes=data.get("changes", 0),
            patch=data.get("patch"),
        )

    @staticmethod
    def _map_finding(
        data: Dict[str, Any],
    ) -> FindingInput:
        return FindingInput(
            analyzer_type=data.get("analyzerType", ""),
            finding_type=data.get("findingType", ""),
            severity=data.get("severity", ""),
            rule_id=data.get("ruleId"),
            title=data.get("title"),
            message=data.get("message"),
            file_path=data.get("filePath"),
            line_number=data.get("lineNumber"),
        )