import math

import pytest

from app.features.extractor import FeatureExtractor
from app.features.input_schema import (
    ChangeSnapshotInput,
    ChangedFileInput,
    FindingInput,
    RiskAnalysisInput,
)
from app.features.normalized_schema import NormalizedFeatureVector
from app.features.normalizer import (
    FeatureNormalizer,
    MAX_RATIO,
)
from app.features.schema import FEATURE_VERSION


def build_features():
    change_snapshot = ChangeSnapshotInput(
        pull_request_number=123,
        owner="example",
        repository="releaseguard",
        title="Test change",
        source_branch="feature/test",
        target_branch="main",
        head_sha="abc123",
        changed_files=[
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
        ],
        total_additions=120,
        total_deletions=30,
        total_changes=150,
    )

    findings = [
        FindingInput(
            analyzer_type="CODE",
            finding_type="CODE_ISSUE",
            severity="HIGH",
        ),
        FindingInput(
            analyzer_type="API",
            finding_type="API_ISSUE",
            severity="CRITICAL",
        ),
    ]

    input_data = RiskAnalysisInput(
        change_snapshot=change_snapshot,
        findings=findings,
    )

    extractor = FeatureExtractor()

    return extractor.extract(input_data)


def test_count_features_use_log1p():
    features = build_features()

    normalizer = FeatureNormalizer()

    normalized = normalizer.normalize(features)

    assert isinstance(
        normalized,
        NormalizedFeatureVector,
    )

    assert normalized.total_additions == pytest.approx(
        math.log1p(120)
    )

    assert normalized.total_deletions == pytest.approx(
        math.log1p(30)
    )

    assert normalized.total_changes == pytest.approx(
        math.log1p(150)
    )

    assert normalized.files_changed == pytest.approx(
        math.log1p(2)
    )


def test_finding_counts_use_log1p():
    features = build_features()

    normalizer = FeatureNormalizer()

    normalized = normalizer.normalize(features)

    assert normalized.code_finding_count == pytest.approx(
        math.log1p(1)
    )

    assert normalized.api_finding_count == pytest.approx(
        math.log1p(1)
    )

    assert normalized.total_finding_count == pytest.approx(
        math.log1p(2)
    )


def test_binary_features_remain_unchanged():
    features = build_features()

    normalizer = FeatureNormalizer()

    normalized = normalizer.normalize(features)

    assert normalized.has_code_findings == 1
    assert normalized.has_api_findings == 1
    assert normalized.has_high_findings == 1
    assert normalized.has_critical_findings == 1

    assert normalized.has_dependency_findings == 0
    assert normalized.has_database_findings == 0
    assert normalized.has_test_impact_findings == 0


def test_ratio_features_are_preserved_when_within_limit():
    features = build_features()

    normalizer = FeatureNormalizer()

    normalized = normalizer.normalize(features)

    assert normalized.change_to_file_ratio == pytest.approx(
        features.change_to_file_ratio
    )

    assert normalized.addition_deletion_ratio == pytest.approx(
        features.addition_deletion_ratio
    )


def test_ratio_features_are_capped():
    features = build_features()

    values = features.to_dict()

    values["change_to_file_ratio"] = 5000.0
    values["addition_deletion_ratio"] = 2000.0

    capped_features = type(features)(
        total_additions=features.total_additions,
        total_deletions=features.total_deletions,
        total_changes=features.total_changes,
        files_changed=features.files_changed,
        files_added=features.files_added,
        files_modified=features.files_modified,
        files_deleted=features.files_deleted,
        code_finding_count=features.code_finding_count,
        dependency_finding_count=features.dependency_finding_count,
        api_finding_count=features.api_finding_count,
        database_finding_count=features.database_finding_count,
        test_impact_finding_count=features.test_impact_finding_count,
        total_finding_count=features.total_finding_count,
        info_finding_count=features.info_finding_count,
        low_finding_count=features.low_finding_count,
        medium_finding_count=features.medium_finding_count,
        high_finding_count=features.high_finding_count,
        critical_finding_count=features.critical_finding_count,
        high_or_critical_finding_count=(
            features.high_or_critical_finding_count
        ),
        has_code_findings=features.has_code_findings,
        has_dependency_findings=features.has_dependency_findings,
        has_api_findings=features.has_api_findings,
        has_database_findings=features.has_database_findings,
        has_test_impact_findings=features.has_test_impact_findings,
        has_high_findings=features.has_high_findings,
        has_critical_findings=features.has_critical_findings,
        change_to_file_ratio=5000.0,
        addition_deletion_ratio=2000.0,
    )

    normalizer = FeatureNormalizer()

    normalized = normalizer.normalize(
        capped_features
    )

    assert normalized.change_to_file_ratio == MAX_RATIO
    assert normalized.addition_deletion_ratio == MAX_RATIO


def test_zero_count_normalizes_to_zero():
    features = build_features()

    zero_features = type(features)(
        total_additions=0,
        total_deletions=0,
        total_changes=0,
        files_changed=0,
        files_added=features.files_added,
        files_modified=features.files_modified,
        files_deleted=features.files_deleted,
        code_finding_count=features.code_finding_count,
        dependency_finding_count=features.dependency_finding_count,
        api_finding_count=features.api_finding_count,
        database_finding_count=features.database_finding_count,
        test_impact_finding_count=features.test_impact_finding_count,
        total_finding_count=0,
        info_finding_count=features.info_finding_count,
        low_finding_count=features.low_finding_count,
        medium_finding_count=features.medium_finding_count,
        high_finding_count=features.high_finding_count,
        critical_finding_count=features.critical_finding_count,
        high_or_critical_finding_count=(
            features.high_or_critical_finding_count
        ),
        has_code_findings=features.has_code_findings,
        has_dependency_findings=features.has_dependency_findings,
        has_api_findings=features.has_api_findings,
        has_database_findings=features.has_database_findings,
        has_test_impact_findings=features.has_test_impact_findings,
        has_high_findings=features.has_high_findings,
        has_critical_findings=features.has_critical_findings,
        change_to_file_ratio=features.change_to_file_ratio,
        addition_deletion_ratio=features.addition_deletion_ratio,
    )

    normalizer = FeatureNormalizer()

    normalized = normalizer.normalize(
        zero_features
    )

    assert normalized.total_additions == 0.0
    assert normalized.total_deletions == 0.0
    assert normalized.total_changes == 0.0
    assert normalized.files_changed == 0.0
    assert normalized.total_finding_count == 0.0


def test_normalization_is_deterministic():
    features = build_features()

    normalizer = FeatureNormalizer()

    first = normalizer.normalize(features)
    second = normalizer.normalize(features)

    assert first == second
    assert first.to_dict() == second.to_dict()


def test_normalization_does_not_mutate_original():
    features = build_features()

    original = features.to_dict()

    normalizer = FeatureNormalizer()

    normalizer.normalize(features)

    assert features.to_dict() == original


def test_feature_version_is_preserved():
    features = build_features()

    normalizer = FeatureNormalizer()

    normalized = normalizer.normalize(features)

    assert isinstance(
        normalized,
        NormalizedFeatureVector,
    )

    assert FEATURE_VERSION == "1.0.0"


def test_negative_count_is_rejected():
    features = build_features()

    invalid_features = type(features)(
        total_additions=-1,
        total_deletions=features.total_deletions,
        total_changes=features.total_changes,
        files_changed=features.files_changed,
        files_added=features.files_added,
        files_modified=features.files_modified,
        files_deleted=features.files_deleted,
        code_finding_count=features.code_finding_count,
        dependency_finding_count=features.dependency_finding_count,
        api_finding_count=features.api_finding_count,
        database_finding_count=features.database_finding_count,
        test_impact_finding_count=features.test_impact_finding_count,
        total_finding_count=features.total_finding_count,
        info_finding_count=features.info_finding_count,
        low_finding_count=features.low_finding_count,
        medium_finding_count=features.medium_finding_count,
        high_finding_count=features.high_finding_count,
        critical_finding_count=features.critical_finding_count,
        high_or_critical_finding_count=(
            features.high_or_critical_finding_count
        ),
        has_code_findings=features.has_code_findings,
        has_dependency_findings=features.has_dependency_findings,
        has_api_findings=features.has_api_findings,
        has_database_findings=features.has_database_findings,
        has_test_impact_findings=features.has_test_impact_findings,
        has_high_findings=features.has_high_findings,
        has_critical_findings=features.has_critical_findings,
        change_to_file_ratio=features.change_to_file_ratio,
        addition_deletion_ratio=features.addition_deletion_ratio,
    )

    normalizer = FeatureNormalizer()

    with pytest.raises(ValueError):
        normalizer.normalize(invalid_features)


def test_invalid_binary_is_rejected():
    features = build_features()

    invalid_features = type(features)(
        total_additions=features.total_additions,
        total_deletions=features.total_deletions,
        total_changes=features.total_changes,
        files_changed=features.files_changed,
        files_added=features.files_added,
        files_modified=features.files_modified,
        files_deleted=features.files_deleted,
        code_finding_count=features.code_finding_count,
        dependency_finding_count=features.dependency_finding_count,
        api_finding_count=features.api_finding_count,
        database_finding_count=features.database_finding_count,
        test_impact_finding_count=features.test_impact_finding_count,
        total_finding_count=features.total_finding_count,
        info_finding_count=features.info_finding_count,
        low_finding_count=features.low_finding_count,
        medium_finding_count=features.medium_finding_count,
        high_finding_count=features.high_finding_count,
        critical_finding_count=features.critical_finding_count,
        high_or_critical_finding_count=(
            features.high_or_critical_finding_count
        ),
        has_code_findings=features.has_code_findings,
        has_dependency_findings=features.has_dependency_findings,
        has_api_findings=features.has_api_findings,
        has_database_findings=features.has_database_findings,
        has_test_impact_findings=features.has_test_impact_findings,
        has_high_findings=features.has_high_findings,
        has_critical_findings=2,
        change_to_file_ratio=features.change_to_file_ratio,
        addition_deletion_ratio=features.addition_deletion_ratio,
    )

    normalizer = FeatureNormalizer()

    with pytest.raises(ValueError):
        normalizer.normalize(invalid_features)