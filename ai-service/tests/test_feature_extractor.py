from app.features.extractor import FeatureExtractor
from app.features.input_schema import (
    ChangeSnapshotInput,
    ChangedFileInput,
    FindingInput,
    RiskAnalysisInput,
)
from app.features.schema import FEATURE_VERSION


def build_input(
    total_additions=0,
    total_deletions=0,
    total_changes=0,
    changed_files=None,
    findings=None,
):
    change_snapshot = ChangeSnapshotInput(
        pull_request_number=123,
        owner="example",
        repository="releaseguard",
        title="Test change",
        source_branch="feature/test",
        target_branch="main",
        head_sha="abc123",
        changed_files=changed_files or [],
        total_additions=total_additions,
        total_deletions=total_deletions,
        total_changes=total_changes,
    )

    return RiskAnalysisInput(
        change_snapshot=change_snapshot,
        findings=findings or [],
    )


def test_feature_extraction():
    changed_files = [
        ChangedFileInput(
            filename="src/PaymentService.java",
            status="modified",
            additions=80,
            deletions=20,
            changes=100,
        ),
        ChangedFileInput(
            filename="src/PaymentController.java",
            status="added",
            additions=40,
            deletions=10,
            changes=50,
        ),
        ChangedFileInput(
            filename="src/OldPayment.java",
            status="deleted",
        ),
    ]

    findings = [
        FindingInput(
            analyzer_type="CODE",
            finding_type="CODE_ISSUE",
            severity="LOW",
        ),
        FindingInput(
            analyzer_type="CODE",
            finding_type="CODE_ISSUE",
            severity="HIGH",
        ),
        FindingInput(
            analyzer_type="DEPENDENCY",
            finding_type="DEPENDENCY_ISSUE",
            severity="MEDIUM",
        ),
        FindingInput(
            analyzer_type="API",
            finding_type="API_ISSUE",
            severity="CRITICAL",
        ),
        FindingInput(
            analyzer_type="DATABASE",
            finding_type="DATABASE_ISSUE",
            severity="HIGH",
        ),
        FindingInput(
            analyzer_type="TEST_IMPACT",
            finding_type="TEST_IMPACT",
            severity="INFO",
        ),
    ]

    input_data = build_input(
        total_additions=120,
        total_deletions=30,
        total_changes=150,
        changed_files=changed_files,
        findings=findings,
    )

    extractor = FeatureExtractor()

    features = extractor.extract(input_data)

    # --------------------------------------------------------------
    # Change magnitude
    # --------------------------------------------------------------

    assert features.total_additions == 120
    assert features.total_deletions == 30
    assert features.total_changes == 150

    assert features.files_changed == 3
    assert features.files_added == 1
    assert features.files_modified == 1
    assert features.files_deleted == 1

    # --------------------------------------------------------------
    # Analyzer counts
    # --------------------------------------------------------------

    assert features.code_finding_count == 2
    assert features.dependency_finding_count == 1
    assert features.api_finding_count == 1
    assert features.database_finding_count == 1
    assert features.test_impact_finding_count == 1

    assert features.total_finding_count == 6

    # --------------------------------------------------------------
    # Severity counts
    # --------------------------------------------------------------

    assert features.info_finding_count == 1
    assert features.low_finding_count == 1
    assert features.medium_finding_count == 1
    assert features.high_finding_count == 2
    assert features.critical_finding_count == 1

    assert features.high_or_critical_finding_count == 3

    # --------------------------------------------------------------
    # Analyzer presence
    # --------------------------------------------------------------

    assert features.has_code_findings == 1
    assert features.has_dependency_findings == 1
    assert features.has_api_findings == 1
    assert features.has_database_findings == 1
    assert features.has_test_impact_findings == 1

    # --------------------------------------------------------------
    # Severity presence
    # --------------------------------------------------------------

    assert features.has_high_findings == 1
    assert features.has_critical_findings == 1

    # --------------------------------------------------------------
    # Derived features
    # --------------------------------------------------------------

    assert features.change_to_file_ratio == 50.0
    assert features.addition_deletion_ratio == 4.0

    # --------------------------------------------------------------
    # Version
    # --------------------------------------------------------------

    assert FEATURE_VERSION == "1.0.0"


def test_empty_findings():
    input_data = build_input(
        total_additions=10,
        total_deletions=5,
        total_changes=15,
        changed_files=[
            ChangedFileInput(
                filename="src/Test.java",
                status="modified",
            )
        ],
        findings=[],
    )

    extractor = FeatureExtractor()

    features = extractor.extract(input_data)

    assert features.total_finding_count == 0

    # Analyzer counts
    assert features.code_finding_count == 0
    assert features.dependency_finding_count == 0
    assert features.api_finding_count == 0
    assert features.database_finding_count == 0
    assert features.test_impact_finding_count == 0

    # Severity counts
    assert features.info_finding_count == 0
    assert features.low_finding_count == 0
    assert features.medium_finding_count == 0
    assert features.high_finding_count == 0
    assert features.critical_finding_count == 0

    assert features.high_or_critical_finding_count == 0

    # Analyzer presence
    assert features.has_code_findings == 0
    assert features.has_dependency_findings == 0
    assert features.has_api_findings == 0
    assert features.has_database_findings == 0
    assert features.has_test_impact_findings == 0

    # Severity presence
    assert features.has_high_findings == 0
    assert features.has_critical_findings == 0


def test_zero_denominator_ratios():
    input_data = build_input(
        total_additions=10,
        total_deletions=0,
        total_changes=10,
        changed_files=[],
        findings=[],
    )

    extractor = FeatureExtractor()

    features = extractor.extract(input_data)

    assert features.change_to_file_ratio == 0.0
    assert features.addition_deletion_ratio == 0.0


def test_missing_change_values_default_to_zero():
    input_data = build_input()

    extractor = FeatureExtractor()

    features = extractor.extract(input_data)

    assert features.total_additions == 0
    assert features.total_deletions == 0
    assert features.total_changes == 0

    assert features.files_changed == 0
    assert features.files_added == 0
    assert features.files_modified == 0
    assert features.files_deleted == 0

    assert features.change_to_file_ratio == 0.0
    assert features.addition_deletion_ratio == 0.0


def test_deterministic_extraction():
    changed_files = [
        ChangedFileInput(
            filename="src/A.java",
            status="modified",
        ),
        ChangedFileInput(
            filename="src/B.java",
            status="added",
        ),
    ]

    findings = [
        FindingInput(
            analyzer_type="CODE",
            finding_type="CODE_ISSUE",
            severity="HIGH",
        ),
        FindingInput(
            analyzer_type="API",
            finding_type="API_ISSUE",
            severity="MEDIUM",
        ),
    ]

    input_data = build_input(
        total_additions=100,
        total_deletions=25,
        total_changes=125,
        changed_files=changed_files,
        findings=findings,
    )

    extractor = FeatureExtractor()

    first = extractor.extract(input_data)
    second = extractor.extract(input_data)

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_feature_vector_to_dict():
    input_data = build_input(
        total_additions=20,
        total_deletions=10,
        total_changes=30,
        changed_files=[
            ChangedFileInput(
                filename="src/A.java",
                status="modified",
            )
        ],
        findings=[
            FindingInput(
                analyzer_type="DATABASE",
                finding_type="DATABASE_ISSUE",
                severity="CRITICAL",
            )
        ],
    )

    extractor = FeatureExtractor()

    features = extractor.extract(input_data)

    result = features.to_dict()

    assert result["feature_version"] == "1.0.0"

    assert result["total_additions"] == 20
    assert result["total_deletions"] == 10
    assert result["total_changes"] == 30

    assert result["files_changed"] == 1
    assert result["database_finding_count"] == 1
    assert result["critical_finding_count"] == 1
    assert result["has_critical_findings"] == 1