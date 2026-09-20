"""CLI tests."""

import pytest
from typer.testing import CliRunner

from otinstaller.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "otinstaller 0.0.1" in result.output


def test_help_contains_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    commands = [
        "install",
        "remove",
        "run",
        "update",
        "list",
        "search",
        "info",
        "example",
        "init",
        "keys",
        "resume",
        "doctor",
    ]
    for cmd in commands:
        assert cmd in result.output


def test_help_no_osint():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "osint" not in result.output.lower()


def test_keys_help():
    result = runner.invoke(app, ["keys", "--help"])
    assert result.exit_code == 0
    assert "Manage API keys." in result.output


@pytest.mark.parametrize(
    "cmd_args",
    [
        ["install", "tool1"],
        ["remove", "tool1"],
        ["update", "tool1"],
        ["list"],
        ["search", "query"],
        ["info", "tool1"],
        ["example", "tool1"],
        ["init"],
        ["keys", "check"],
        ["resume"],
        ["doctor"],
    ],
)
def test_stub_commands_exit_2(cmd_args):
    result = runner.invoke(app, cmd_args)
    assert result.exit_code == 2
    assert "not implemented yet" in result.output


def test_run_with_extra_args():
    result = runner.invoke(app, ["run", "sherlock", "--", "someuser", "--timeout", "5"])
    assert result.exit_code == 2
    assert "not implemented yet" in result.output
