"""Init command tests."""

from typer.testing import CliRunner

from otinstaller.cli import app

runner = CliRunner()


def test_init_creates_directories_and_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    result = runner.invoke(app, ["init", "--yes"])
    assert result.exit_code == 0
    assert (tmp_path / "tools").exists()
    assert (tmp_path / "logs").exists()
    assert (tmp_path / ".env").exists()
    assert (tmp_path / "accepted.json").exists()


def test_init_runs_twice(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    result = runner.invoke(app, ["init", "--yes"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["init", "--yes"])
    assert result.exit_code == 0


def test_init_fixes_env_permissions(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    # Create env file with loose permissions
    env = tmp_path / ".env"
    env.write_text("KEY=value\n")
    env.chmod(0o644)
    result = runner.invoke(app, ["init", "--yes"])
    assert result.exit_code == 0
    assert "fixed permissions" in result.output


def test_init_refuses_without_yes_when_not_tty(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    result = runner.invoke(app, ["init"], input="")
    assert result.exit_code == 1
    assert "confirmation needed" in result.output


def test_init_accepts_with_yes(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    result = runner.invoke(app, ["init", "--yes"])
    assert result.exit_code == 0


def test_init_env_contents_not_printed(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    result = runner.invoke(app, ["init", "--yes"])
    assert "API keys" not in result.output  # contents not printed
    env = tmp_path / ".env"
    content = env.read_text()
    assert "# API keys for tools managed by otinstaller." in content
    assert "# Add one KEY=value per line. Keep this file private." in content
