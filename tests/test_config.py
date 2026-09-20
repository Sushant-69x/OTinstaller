"""Config tests."""

from pathlib import Path

from otinstaller.config import ensure_dir, get_env_file, get_home, get_results_dir


def test_get_home_default(monkeypatch):
    monkeypatch.delenv("OTINSTALLER_HOME", raising=False)
    home = get_home()
    assert str(home).endswith(".otinstaller")


def test_get_home_env(monkeypatch, tmp_path):
    custom = tmp_path / "custom_home"
    monkeypatch.setenv("OTINSTALLER_HOME", str(custom))
    home = get_home()
    assert home == custom


def test_get_results_dir_default(monkeypatch):
    monkeypatch.delenv("OTINSTALLER_RESULTS_DIR", raising=False)
    results = get_results_dir()
    assert results == Path.cwd() / "results"


def test_get_results_dir_env(monkeypatch, tmp_path):
    custom = tmp_path / "custom_results"
    monkeypatch.setenv("OTINSTALLER_RESULTS_DIR", str(custom))
    results = get_results_dir()
    assert results == custom


def test_get_env_file():
    env_file = get_env_file()
    assert env_file == get_home() / ".env"


def test_ensure_dir_creates_nested(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    result = ensure_dir(nested)
    assert result == nested
    assert nested.exists()
    assert nested.is_dir()


def test_ensure_dir_idempotent(tmp_path):
    dir_path = tmp_path / "testdir"
    ensure_dir(dir_path)
    result = ensure_dir(dir_path)
    assert result == dir_path
    assert dir_path.exists()
