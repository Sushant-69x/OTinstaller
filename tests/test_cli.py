"""CLI tests."""

import sys

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
        ["update", "tool1"],
        ["example", "tool1"],
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


def make_registry_yaml(tmp_path, tools_data):
    import yaml

    reg = tmp_path / "registry.yaml"
    reg.write_text(yaml.dump({"tools": tools_data}))
    return reg


def test_list_table(monkeypatch, tmp_path):
    tools = [
        {
            "name": "sherlock",
            "display_name": "Sherlock",
            "description": "Search usernames",
            "install": {
                "method": "pip",
                "package": "sherlock-project",
            },
            "entrypoint": {"command": "sherlock"},
            "capabilities": ["username-search"],
        }
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "sherlock" in result.output
    assert "username-search" not in result.output
    assert "1 tool" in result.output


def test_list_json(monkeypatch, tmp_path):
    tools = [
        {
            "name": "sherlock",
            "display_name": "Sherlock",
            "description": "Search usernames",
            "install": {
                "method": "pip",
                "package": "sherlock-project",
            },
            "entrypoint": {"command": "sherlock"},
            "capabilities": ["username-search"],
        }
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    import json

    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["name"] == "sherlock"
    assert data[0]["capabilities"] == ["username-search"]


def test_list_empty(monkeypatch, tmp_path):
    reg = make_registry_yaml(tmp_path, [])
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "no tools in the registry" in result.output


def test_list_empty_json(monkeypatch, tmp_path):
    reg = make_registry_yaml(tmp_path, [])
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    import json

    data = json.loads(result.output)
    assert data == []


def test_list_installed(monkeypatch, tmp_path):
    # Use a temp OTINSTALLER_HOME for state DB
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    reg = make_registry_yaml(tmp_path, [])
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["list", "--installed"])
    assert result.exit_code == 0
    assert "no tools installed" in result.output


def test_list_installed_json(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    reg = make_registry_yaml(tmp_path, [])
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["list", "--installed", "--json"])
    assert result.exit_code == 0
    import json

    data = json.loads(result.output)
    assert data == []


def test_search(monkeypatch, tmp_path):
    tools = [
        {
            "name": "sherlock",
            "display_name": "Sherlock",
            "description": "Search usernames",
            "install": {
                "method": "pip",
                "package": "sherlock-project",
            },
            "entrypoint": {"command": "sherlock"},
            "capabilities": ["username-search"],
        },
        {
            "name": "maigret",
            "display_name": "Maigret",
            "description": "Build profile",
            "install": {
                "method": "pip",
                "package": "maigret",
            },
            "entrypoint": {"command": "maigret"},
            "capabilities": ["username-search"],
        },
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["search", "username"])
    assert result.exit_code == 0
    assert "sherlock" in result.output
    assert "maigret" in result.output
    assert "2 tools" in result.output


def test_search_no_match(monkeypatch, tmp_path):
    tools = [
        {
            "name": "sherlock",
            "display_name": "Sherlock",
            "description": "Search usernames",
            "install": {
                "method": "pip",
                "package": "sherlock-project",
            },
            "entrypoint": {"command": "sherlock"},
        }
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["search", "email"])
    assert result.exit_code == 0
    assert "no tools match 'email'" in result.output


def test_search_single_match(monkeypatch, tmp_path):
    tools = [
        {
            "name": "sherlock",
            "display_name": "Sherlock",
            "description": "Search usernames",
            "install": {
                "method": "pip",
                "package": "sherlock-project",
            },
            "entrypoint": {"command": "sherlock"},
            "capabilities": ["username-search"],
        },
        {
            "name": "maigret",
            "display_name": "Maigret",
            "description": "Build profile",
            "install": {
                "method": "pip",
                "package": "maigret",
            },
            "entrypoint": {"command": "maigret"},
            "capabilities": ["username-search"],
        },
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["search", "maigret"])
    assert result.exit_code == 0
    assert "maigret" in result.output
    assert "sherlock" not in result.output
    assert "1 tool" in result.output


def test_search_json(monkeypatch, tmp_path):
    tools = [
        {
            "name": "sherlock",
            "display_name": "Sherlock",
            "description": "Search usernames",
            "install": {
                "method": "pip",
                "package": "sherlock-project",
            },
            "entrypoint": {"command": "sherlock"},
            "capabilities": ["username-search"],
        }
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["search", "username", "--json"])
    assert result.exit_code == 0
    import json

    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["name"] == "sherlock"


def test_info(monkeypatch, tmp_path):
    tools = [
        {
            "name": "sherlock",
            "display_name": "Sherlock",
            "description": "Search usernames",
            "repo": "sherlock-project/sherlock",
            "license": "MIT",
            "install": {
                "method": "pip",
                "package": "sherlock-project",
            },
            "entrypoint": {"command": "sherlock"},
            "capabilities": ["username-search"],
        }
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["info", "sherlock"])
    assert result.exit_code == 0
    assert "Sherlock (sherlock)" in result.output
    assert "Search usernames" in result.output
    assert "Tier: community" in result.output
    assert "Repo: sherlock-project/sherlock" in result.output
    assert "License: MIT" in result.output
    assert "Install: pip sherlock-project" in result.output
    assert "Entrypoint: sherlock" in result.output
    assert "Capabilities: username-search" in result.output
    assert "API keys: none" in result.output
    assert "Not verified yet" in result.output


def test_info_case_insensitive(monkeypatch, tmp_path):
    tools = [
        {
            "name": "sherlock",
            "display_name": "Sherlock",
            "description": "Search usernames",
            "install": {
                "method": "pip",
                "package": "sherlock-project",
            },
            "entrypoint": {"command": "sherlock"},
        }
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["info", "SHERLOCK"])
    assert result.exit_code == 0
    assert "Sherlock" in result.output


def test_info_unknown_tool(monkeypatch, tmp_path):
    tools = [
        {
            "name": "sherlock",
            "display_name": "Sherlock",
            "description": "Search usernames",
            "install": {
                "method": "pip",
                "package": "sherlock-project",
            },
            "entrypoint": {"command": "sherlock"},
        }
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["info", "sherlok"])
    assert result.exit_code == 1
    assert "error: unknown tool 'sherlok'" in result.output
    assert "did you mean: sherlock?" in result.output


def test_info_json(monkeypatch, tmp_path):
    tools = [
        {
            "name": "sherlock",
            "display_name": "Sherlock",
            "description": "Search usernames",
            "install": {
                "method": "pip",
                "package": "sherlock-project",
            },
            "entrypoint": {"command": "sherlock"},
            "capabilities": ["username-search"],
        }
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["info", "sherlock", "--json"])
    assert result.exit_code == 0
    import json

    data = json.loads(result.output)
    assert data["name"] == "sherlock"
    assert data["capabilities"] == ["username-search"]


def test_info_dual_use_notice(monkeypatch, tmp_path):
    tools = [
        {
            "name": "dualtool",
            "display_name": "Dual Tool",
            "description": "A dual use tool",
            "install": {
                "method": "pip",
                "package": "dualtool",
            },
            "entrypoint": {"command": "dualtool"},
            "capabilities": ["dual-use"],
        }
    ]
    reg = make_registry_yaml(tmp_path, tools)
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["info", "dualtool"])
    assert result.exit_code == 0
    assert "Dual-use tool. See the responsible use notice in the README." in result.output


def test_broken_registry_error(monkeypatch, tmp_path):
    reg = tmp_path / "bad.yaml"
    reg.write_text("invalid: yaml: [")
    monkeypatch.setenv("OTINSTALLER_REGISTRY", str(reg))

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 1
    assert "error:" in result.output


def test_install_refuses_on_non_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    result = runner.invoke(app, ["install", "sherlock"])
    assert result.exit_code == 1
    assert "error: otinstaller currently supports Linux only" in result.output


def test_remove_refuses_on_non_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    result = runner.invoke(app, ["remove", "sherlock"])
    assert result.exit_code == 1
    assert "error: otinstaller currently supports Linux only" in result.output


def test_help_no_osint_still():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "osint" not in result.output.lower()
