import math

from app.features.normalized_schema import NormalizedFeatureVector
from app.features.schema import FeatureVector


MAX_RATIO = 1000.0


class FeatureNormalizer:
    """
    Deterministic normalization for ReleaseGuard V0.5 features.

    Rules:
    - Count/magnitude features -> log1p
    - Binary features -> unchanged
    - Ratio features -> bounded to MAX_RATIO
    - Original FeatureVector is never mutated
    """

    COUNT_FEATURES = (
        "total_additions",
        "total_deletions",
        "total_changes",
        "files_changed",
        "files_added",
        "files_modified",
        "files_deleted",
        "code_finding_count",
        "dependency_finding_count",
        "api_finding_count",
        "database_finding_count",
        "test_impact_finding_count",
        "total_finding_count",
        "info_finding_count",
        "low_finding_count",
        "medium_finding_count",
        "high_finding_count",
        "critical_finding_count",
        "high_or_critical_finding_count",
    )

    RATIO_FEATURES = (
        "change_to_file_ratio",
        "addition_deletion_ratio",
    )

    BINARY_FEATURES = (
        "has_code_findings",
        "has_dependency_findings",
        "has_api_findings",
        "has_database_findings",
        "has_test_impact_findings",
        "has_high_findings",
        "has_critical_findings",
    )

    def normalize(
        self,
        features: FeatureVector,
    ) -> NormalizedFeatureVector:
        """
        Create a normalized ML-ready feature vector from the
        supplied raw FeatureVector.

        The original FeatureVector is never modified.
        """

        return NormalizedFeatureVector(
            # ----------------------------------------------------------
            # Change magnitude
            # ----------------------------------------------------------

            total_additions=self._log1p(
                features.total_additions
            ),
            total_deletions=self._log1p(
                features.total_deletions
            ),
            total_changes=self._log1p(
                features.total_changes
            ),

            files_changed=self._log1p(
                features.files_changed
            ),
            files_added=self._log1p(
                features.files_added
            ),
            files_modified=self._log1p(
                features.files_modified
            ),
            files_deleted=self._log1p(
                features.files_deleted
            ),

            # ----------------------------------------------------------
            # Analyzer finding counts
            # ----------------------------------------------------------

            code_finding_count=self._log1p(
                features.code_finding_count
            ),
            dependency_finding_count=self._log1p(
                features.dependency_finding_count
            ),
            api_finding_count=self._log1p(
                features.api_finding_count
            ),
            database_finding_count=self._log1p(
                features.database_finding_count
            ),
            test_impact_finding_count=self._log1p(
                features.test_impact_finding_count
            ),

            total_finding_count=self._log1p(
                features.total_finding_count
            ),

            # ----------------------------------------------------------
            # Severity counts
            # ----------------------------------------------------------

            info_finding_count=self._log1p(
                features.info_finding_count
            ),
            low_finding_count=self._log1p(
                features.low_finding_count
            ),
            medium_finding_count=self._log1p(
                features.medium_finding_count
            ),
            high_finding_count=self._log1p(
                features.high_finding_count
            ),
            critical_finding_count=self._log1p(
                features.critical_finding_count
            ),

            high_or_critical_finding_count=self._log1p(
                features.high_or_critical_finding_count
            ),

            # ----------------------------------------------------------
            # Analyzer presence indicators
            # ----------------------------------------------------------

            has_code_findings=self._normalize_binary(
                features.has_code_findings
            ),
            has_dependency_findings=self._normalize_binary(
                features.has_dependency_findings
            ),
            has_api_findings=self._normalize_binary(
                features.has_api_findings
            ),
            has_database_findings=self._normalize_binary(
                features.has_database_findings
            ),
            has_test_impact_findings=self._normalize_binary(
                features.has_test_impact_findings
            ),

            # ----------------------------------------------------------
            # Severity presence indicators
            # ----------------------------------------------------------

            has_high_findings=self._normalize_binary(
                features.has_high_findings
            ),
            has_critical_findings=self._normalize_binary(
                features.has_critical_findings
            ),

            # ----------------------------------------------------------
            # Derived features
            # ----------------------------------------------------------

            change_to_file_ratio=self._normalize_ratio(
                features.change_to_file_ratio
            ),
            addition_deletion_ratio=self._normalize_ratio(
                features.addition_deletion_ratio
            ),
        )

    @staticmethod
    def _log1p(value: float) -> float:
        """
        Apply log1p to a non-negative numeric feature.

        log1p(x) = log(1 + x)

        This safely maps zero to zero.
        """

        if value < 0:
            raise ValueError(
                "Count features must not be negative"
            )

        return math.log1p(value)

    @staticmethod
    def _normalize_ratio(value: float) -> float:
        """
        Bound a ratio to the deterministic range [0, MAX_RATIO].
        """

        if value < 0:
            raise ValueError(
                "Ratio features must not be negative"
            )

        return min(float(value), MAX_RATIO)

    @staticmethod
    def _normalize_binary(value: int) -> int:
        """
        Binary features must remain exactly 0 or 1.
        """

        if value not in (0, 1):
            raise ValueError(
                "Binary features must be either 0 or 1"
            )

        return value