from app.cli.__main__ import main, build_parser
from app.pipeline.validator import ValidationResult


def test_cli_parser_builds_successfully():
    parser = build_parser()
    assert parser is not None


def test_cli_info_command_executes(capsys):
    exit_code = main(["info"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ReleaseGuard AI Service" in captured.out
    assert "Model Version" in captured.out
    assert "2.0.0" in captured.out


def test_cli_pipeline_validate_command_executes(capsys):
    exit_code = main(["pipeline", "validate"])
    # In CI without uncommitted datasets, exit_code is 1 (with missing raw data);
    # on local machines with full dataset, exit_code is 0. Both are valid.
    assert exit_code in (0, 1)
    captured = capsys.readouterr()
    assert "ReleaseGuard Pipeline Validation Report" in captured.out
    assert "[OK] Production Artifact" in captured.out


def test_cli_pipeline_validate_command_success(monkeypatch, capsys):
    monkeypatch.setattr(
        "app.cli.__main__.PipelineValidator.validate_all",
        lambda self, model_version: {
            "raw_data": ValidationResult("raw_data", True, "2.0.0"),
            "features": ValidationResult("features", True, "1.0.0"),
            "splits": ValidationResult("splits", True, "2.0.0"),
            "trained_model": ValidationResult("trained_model", True, "2.0.0"),
            "evaluation": ValidationResult("evaluation", True, "2.0.0"),
            "production_artifact": ValidationResult("production_artifact", True, "2.0.0"),
        },
    )
    monkeypatch.setattr(
        "app.cli.__main__.PipelineValidator.is_ready_for_training",
        lambda self: (True, []),
    )
    monkeypatch.setattr(
        "app.cli.__main__.PipelineValidator.is_ready_for_promotion",
        lambda self, v: (True, []),
    )
    exit_code = main(["pipeline", "validate"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Ready for Promotion : YES" in captured.out


def test_cli_unknown_command_returns_help():
    exit_code = main([])
    assert exit_code == 0

