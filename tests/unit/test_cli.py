from mediawg_dashboard.cli import cmd_brief, main


def test_brief_command_returns_zero():
    assert cmd_brief() == 0


def test_no_args_returns_nonzero():
    assert main([]) != 0


def test_unknown_command_returns_nonzero():
    assert main(["wat"]) != 0
