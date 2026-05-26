from mediawg_dashboard.cli import main


def test_refresh_command_returns_zero():
    assert main(["refresh"]) == 0


def test_brief_command_returns_zero():
    assert main(["brief"]) == 0


def test_no_args_returns_nonzero():
    assert main([]) != 0


def test_unknown_command_returns_nonzero():
    assert main(["wat"]) != 0
