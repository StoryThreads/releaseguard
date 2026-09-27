from dataclasses import dataclass


FEATURE_VERSION = "1.0.0"


@dataclass(frozen=True)
class FeatureVector:
    """
    ReleaseGuard ML feature vector.

    Feature schema version: 1.0.0
    """

    # ------------------------------------------------------------------
    # Change magnitude
    # ------------------------------------------------------------------

    total_additions: int
    total_deletions: int
    total_changes: int

    files_changed: int
    files_added: int
    files_modified: int
    files_deleted: int

    # ------------------------------------------------------------------
    # Analyzer finding counts
    # ------------------------------------------------------------------

    code_finding_count: int
    dependency_finding_count: int
    api_finding_count: int
    database_finding_count: int
    test_impact_finding_count: int

    total_finding_count: int

    # ------------------------------------------------------------------
    # Severity counts
    # ------------------------------------------------------------------

    info_finding_count: int
    low_finding_count: int
    medium_finding_count: int
    high_finding_count: int
    critical_finding_count: int

    high_or_critical_finding_count: int

    # ------------------------------------------------------------------
    # Analyzer presence indicators
    # ------------------------------------------------------------------

    has_code_findings: int
    has_dependency_findings: int
    has_api_findings: int
    has_database_findings: int
    has_test_impact_findings: int

    # ------------------------------------------------------------------
    # Severity presence indicators
    # ------------------------------------------------------------------

    has_high_findings: int
    has_critical_findings: int

    # ------------------------------------------------------------------
    # Derived change features
    # ------------------------------------------------------------------

    change_to_file_ratio: float
    addition_deletion_ratio: float

    def to_dict(self) -> dict:
        """
        Convert the feature vector into a plain dictionary.

        The dictionary is suitable for JSON serialization and
        downstream ML processing.
        """
        return {
            "feature_version": FEATURE_VERSION,

            "total_additions": self.total_additions,
            "total_deletions": self.total_deletions,
            "total_changes": self.total_changes,

            "files_changed": self.files_changed,
            "files_added": self.files_added,
            "files_modified": self.files_modified,
            "files_deleted": self.files_deleted,

            "code_finding_count": self.code_finding_count,
            "dependency_finding_count": self.dependency_finding_count,
            "api_finding_count": self.api_finding_count,
            "database_finding_count": self.database_finding_count,
            "test_impact_finding_count": self.test_impact_finding_count,
            "total_finding_count": self.total_finding_count,

            "info_finding_count": self.info_finding_count,
            "low_finding_count": self.low_finding_count,
            "medium_finding_count": self.medium_finding_count,
            "high_finding_count": self.high_finding_count,
            "critical_finding_count": self.critical_finding_count,
            "high_or_critical_finding_count": (
                self.high_or_critical_finding_count
            ),

            "has_code_findings": self.has_code_findings,
            "has_dependency_findings": self.has_dependency_findings,
            "has_api_findings": self.has_api_findings,
            "has_database_findings": self.has_database_findings,
            "has_test_impact_findings": self.has_test_impact_findings,

            "has_high_findings": self.has_high_findings,
            "has_critical_findings": self.has_critical_findings,

            "change_to_file_ratio": self.change_to_file_ratio,
            "addition_deletion_ratio": self.addition_deletion_ratio,
        }