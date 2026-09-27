from app.features.input_mapper import InputMapper


def test_java_json_maps_to_python_contract():
    payload = {
        "changeSnapshot": {
            "pullRequestNumber": 123,
            "owner": "example",
            "repository": "releaseguard",
            "title": "Update payment API",
            "sourceBranch": "feature/payment",
            "targetBranch": "main",
            "headSha": "abc123",
            "changedFiles": [
                {
                    "filename": "src/PaymentService.java",
                    "status": "modified",
                    "additions": 80,
                    "deletions": 20,
                    "changes": 100,
                    "patch": "@@ -1 +1 @@",
                }
            ],
            "totalAdditions": 80,
            "totalDeletions": 20,
            "totalChanges": 100,
        },
        "findings": [
            {
                "analyzerType": "CODE",
                "findingType": "CODE_ISSUE",
                "severity": "HIGH",
                "ruleId": "CODE-001",
                "title": "Test finding",
                "message": "Example finding",
                "filePath": "src/PaymentService.java",
                "lineNumber": 42,
            }
        ],
    }

    result = InputMapper.from_dict(payload)

    assert result.change_snapshot.pull_request_number == 123
    assert result.change_snapshot.owner == "example"
    assert result.change_snapshot.repository == "releaseguard"

    assert result.change_snapshot.source_branch == "feature/payment"
    assert result.change_snapshot.target_branch == "main"
    assert result.change_snapshot.head_sha == "abc123"

    assert result.change_snapshot.total_additions == 80
    assert result.change_snapshot.total_deletions == 20
    assert result.change_snapshot.total_changes == 100

    assert len(result.change_snapshot.changed_files) == 1

    changed_file = result.change_snapshot.changed_files[0]

    assert changed_file.filename == "src/PaymentService.java"
    assert changed_file.status == "modified"
    assert changed_file.additions == 80
    assert changed_file.deletions == 20
    assert changed_file.changes == 100
    assert changed_file.patch == "@@ -1 +1 @@"

    assert len(result.findings) == 1

    finding = result.findings[0]

    assert finding.analyzer_type == "CODE"
    assert finding.finding_type == "CODE_ISSUE"
    assert finding.severity == "HIGH"
    assert finding.rule_id == "CODE-001"
    assert finding.title == "Test finding"
    assert finding.message == "Example finding"
    assert finding.file_path == "src/PaymentService.java"
    assert finding.line_number == 42


def test_missing_optional_values_are_handled():
    payload = {
        "changeSnapshot": {
            "changedFiles": []
        },
        "findings": [],
    }

    result = InputMapper.from_dict(payload)

    assert result.change_snapshot.pull_request_number is None
    assert result.change_snapshot.owner is None
    assert result.change_snapshot.repository is None

    assert result.change_snapshot.total_additions == 0
    assert result.change_snapshot.total_deletions == 0
    assert result.change_snapshot.total_changes == 0

    assert result.change_snapshot.changed_files == []
    assert result.findings == []


def test_multiple_findings_are_mapped():
    payload = {
        "changeSnapshot": {
            "changedFiles": []
        },
        "findings": [
            {
                "analyzerType": "CODE",
                "findingType": "CODE_ISSUE",
                "severity": "LOW",
            },
            {
                "analyzerType": "API",
                "findingType": "API_ISSUE",
                "severity": "CRITICAL",
            },
            {
                "analyzerType": "DATABASE",
                "findingType": "DATABASE_ISSUE",
                "severity": "HIGH",
            },
        ],
    }

    result = InputMapper.from_dict(payload)

    assert len(result.findings) == 3

    assert result.findings[0].analyzer_type == "CODE"
    assert result.findings[0].severity == "LOW"

    assert result.findings[1].analyzer_type == "API"
    assert result.findings[1].severity == "CRITICAL"

    assert result.findings[2].analyzer_type == "DATABASE"
    assert result.findings[2].severity == "HIGH"