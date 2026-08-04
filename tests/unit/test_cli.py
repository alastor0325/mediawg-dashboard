from mediawg_dashboard.cli import _safe, cmd_brief, main


def test_brief_command_returns_zero():
    assert cmd_brief() == 0


def test_safe_returns_the_value_on_success():
    failed: set[str] = set()
    assert _safe("x", lambda: 42, None, failed, "k") == 42
    assert failed == set()


def test_safe_degrades_and_records_the_failure_key():
    failed: set[str] = set()

    def boom():
        raise RuntimeError("api down")

    assert _safe("x", boom, None, failed, "k") is None
    assert failed == {"k"}


def test_safe_shares_one_key_across_several_calls():
    """The three activity calls all record "activity", so any one failing marks
    the whole axis unknown instead of reporting a partial count."""
    failed: set[str] = set()

    def boom():
        raise RuntimeError("api down")

    _safe("a", lambda: [1], None, failed, "activity")
    _safe("b", boom, None, failed, "activity")
    assert failed == {"activity"}


def test_no_args_returns_nonzero():
    assert main([]) != 0


def test_unknown_command_returns_nonzero():
    assert main(["wat"]) != 0
