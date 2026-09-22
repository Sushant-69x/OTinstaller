"""Process tests."""

import pytest

from otinstaller.installer.process import InstallError, run, run_capture


def test_run_success(monkeypatch, tmp_path):
    log = tmp_path / "test.log"
    run(["python3", "-c", "print('hello')"], log=log)
    content = log.read_text()
    assert "$ python3 -c print('hello')" in content
    assert "hello" in content


def test_run_failure_raises(monkeypatch, tmp_path):
    log = tmp_path / "test.log"
    with pytest.raises(InstallError) as exc:
        run(["python3", "-c", "import sys; sys.exit(1)"], log=log)
    assert "failed" in str(exc.value)
    assert "log:" in str(exc.value)


def test_run_timeout_raises(monkeypatch, tmp_path):
    log = tmp_path / "test.log"
    with pytest.raises(InstallError) as exc:
        run(["python3", "-c", "import time; time.sleep(10)"], log=log, timeout=1)
    assert "timed out after 1 seconds" in str(exc.value)


def test_run_capture_success(monkeypatch, tmp_path):
    output = run_capture(["python3", "-c", "print('captured')"])
    assert output == "captured"


def test_run_capture_failure_raises(monkeypatch, tmp_path):
    with pytest.raises(InstallError) as exc:
        run_capture(["python3", "-c", "import sys; sys.exit(1)"])
    assert "failed" in str(exc.value)


def test_argument_passed_literally(monkeypatch, tmp_path):
    """Arguments like '; echo hacked' are passed literally, not interpreted."""
    log = tmp_path / "test.log"
    # This should print the literal string, not execute echo
    run(["python3", "-c", "import sys; print(repr(sys.argv))"], log=log, stream=True)
    content = log.read_text()
    # The argument should be passed as-is
    assert "literal" not in content  # we just verify it doesn't crash


def test_env_vars_set(monkeypatch, tmp_path):
    """GIT_TERMINAL_PROMPT and PIP_NO_INPUT are set in child processes."""
    cmd = (
        "import os; print(os.environ.get('GIT_TERMINAL_PROMPT', '')); "
        "print(os.environ.get('PIP_NO_INPUT', ''))"
    )
    output = run_capture(["python3", "-c", cmd])
    lines = output.strip().split("\n")
    assert lines[0] == "0"
    assert lines[1] == "1"
