from app.cli.__main__ import main, build_parser


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
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ReleaseGuard Pipeline Validation Report" in captured.out
    assert "[OK] Production Artifact" in captured.out
    assert "Ready for Promotion : YES" in captured.out


def test_cli_unknown_command_returns_help():
    exit_code = main([])
    assert exit_code == 0
