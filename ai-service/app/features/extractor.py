from collections import Counter

from app.features.input_schema import RiskAnalysisInput
from app.features.schema import FeatureVector


class FeatureExtractor:
    """
    Extracts deterministic ML features from the ReleaseGuard
    V0.5 raw ML input contract.

    Feature schema: 1.0.0
    """

    def extract(
        self,
        input_data: RiskAnalysisInput,
    ) -> FeatureVector:
        """
        Convert ChangeSnapshot + Findings into a FeatureVector.
        """

        change_snapshot = input_data.change_snapshot
        findings = input_data.findings

        changed_files = change_snapshot.changed_files

        # --------------------------------------------------------------
        # Change magnitude
        # --------------------------------------------------------------

        total_additions = self._non_negative_int(
            change_snapshot.total_additions
        )

        total_deletions = self._non_negative_int(
            change_snapshot.total_deletions
        )

        total_changes = self._non_negative_int(
            change_snapshot.total_changes
        )

        files_changed = len(changed_files)

        files_added = self._count_file_status(
            changed_files,
            "added",
        )

        files_modified = self._count_file_status(
            changed_files,
            "modified",
        )

        files_deleted = self._count_file_status(
            changed_files,
            "deleted",
        )

        # --------------------------------------------------------------
        # Analyzer and severity aggregates
        # --------------------------------------------------------------

        analyzer_counts = Counter()
        severity_counts = Counter()

        for finding in findings:
            analyzer_type = self._normalize_value(
                finding.analyzer_type
            )
    
            severity = self._normalize_value(
                finding.severity
            )

            if analyzer_type:
                analyzer_counts[analyzer_type] += 1

            if severity:
                severity_counts[severity] += 1

        # --------------------------------------------------------------
        # Analyzer counts
        # --------------------------------------------------------------

        code_finding_count = analyzer_counts["CODE"]

        dependency_finding_count = analyzer_counts["DEPENDENCY"]

        api_finding_count = analyzer_counts["API"]

        database_finding_count = analyzer_counts["DATABASE"]

        test_impact_finding_count = analyzer_counts["TEST_IMPACT"]

        total_finding_count = len(findings)

        # --------------------------------------------------------------
        # Severity counts
        # --------------------------------------------------------------

        info_finding_count = severity_counts["INFO"]

        low_finding_count = severity_counts["LOW"]

        medium_finding_count = severity_counts["MEDIUM"]

        high_finding_count = severity_counts["HIGH"]

        critical_finding_count = severity_counts["CRITICAL"]

        high_or_critical_finding_count = (
            high_finding_count + critical_finding_count
        )

        # --------------------------------------------------------------
        # Analyzer presence indicators
        # --------------------------------------------------------------

        has_code_findings = self._indicator(
            code_finding_count
        )

        has_dependency_findings = self._indicator(
            dependency_finding_count
        )

        has_api_findings = self._indicator(
            api_finding_count
        )

        has_database_findings = self._indicator(
            database_finding_count
        )

        has_test_impact_findings = self._indicator(
            test_impact_finding_count
        )

        # --------------------------------------------------------------
        # Severity presence indicators
        # --------------------------------------------------------------

        has_high_findings = self._indicator(
            high_finding_count
        )

        has_critical_findings = self._indicator(
            critical_finding_count
        )

        # --------------------------------------------------------------
        # Derived features
        # --------------------------------------------------------------

        change_to_file_ratio = self._safe_ratio(
            total_changes,
            files_changed,
        )

        addition_deletion_ratio = self._safe_ratio(
            total_additions,
            total_deletions,
        )

        # --------------------------------------------------------------
        # Feature vector
        # --------------------------------------------------------------

        return FeatureVector(
            total_additions=total_additions,
            total_deletions=total_deletions,
            total_changes=total_changes,

            files_changed=files_changed,
            files_added=files_added,
            files_modified=files_modified,
            files_deleted=files_deleted,

            code_finding_count=code_finding_count,
            dependency_finding_count=dependency_finding_count,
            api_finding_count=api_finding_count,
            database_finding_count=database_finding_count,
            test_impact_finding_count=test_impact_finding_count,
            total_finding_count=total_finding_count,

            info_finding_count=info_finding_count,
            low_finding_count=low_finding_count,
            medium_finding_count=medium_finding_count,
            high_finding_count=high_finding_count,
            critical_finding_count=critical_finding_count,
            high_or_critical_finding_count=(
                high_or_critical_finding_count
            ),

            has_code_findings=has_code_findings,
            has_dependency_findings=has_dependency_findings,
            has_api_findings=has_api_findings,
            has_database_findings=has_database_findings,
            has_test_impact_findings=has_test_impact_findings,

            has_high_findings=has_high_findings,
            has_critical_findings=has_critical_findings,

            change_to_file_ratio=change_to_file_ratio,
            addition_deletion_ratio=addition_deletion_ratio,
        )

    # ==================================================================
    # Helpers
    # ==================================================================

    @staticmethod
    def _non_negative_int(value) -> int:
        if value is None:
            return 0

        try:
            number = int(value)
        except (TypeError, ValueError):
            return 0

        return max(number, 0)

    @staticmethod
    def _count_file_status(
        changed_files,
        status: str,
    ) -> int:
        return sum(
            1
            for changed_file in changed_files
            if FeatureExtractor._normalize_value(
                changed_file.status
            ) == status.upper()
        )

    @staticmethod
    def _normalize_value(value) -> str:
        if value is None:
            return ""

        return str(value).strip().upper()

    @staticmethod
    def _indicator(count: int) -> int:
        return 1 if count > 0 else 0

    @staticmethod
    def _safe_ratio(
        numerator: int,
        denominator: int,
    ) -> float:
        if denominator <= 0:
            return 0.0

        return numerator / denominator