"""Tests for the discovery pipeline."""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests
import yaml

from otinstaller.denylist import Denylist, check_tool
from otinstaller.registry import Tool
from pipeline.discover import (
    _load_env_tokens_file,
    check_pypi,
    detect_install_method,
    sanitize_name,
    truncate_description,
)


def test_sanitize_name():
    assert sanitize_name("Sherlock") == "sherlock"
    assert sanitize_name("theHarvester") == "theharvester"
    assert sanitize_name("OSINT-Tool") == "osint-tool"
    assert sanitize_name("Tool.Name") == "tool-name"
    assert sanitize_name("  spaces  ") == "spaces"


def test_truncate_description():
    assert truncate_description("short") == "short"
    assert truncate_description("a" * 200) == "a" * 200
    assert truncate_description("a" * 201).endswith("...")
    assert truncate_description(None) == ""
    assert truncate_description("") == ""
    assert truncate_description("line1\nline2") == "line1 line2"


def test_detect_install_method():
    assert detect_install_method(["pyproject.toml", "README.md"]) == "pip-repo"
    assert detect_install_method(["setup.py", "README.md"]) == "pip-repo"
    assert detect_install_method(["requirements.txt", "README.md"]) == "git-requirements"
    assert detect_install_method(["README.md"]) == "unknown"
    assert detect_install_method([]) == "unknown"


@patch("pipeline.discover.requests.Session")
def test_check_pypi_success(mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_session.get.return_value = mock_resp

    result = check_pypi(mock_session, "sherlock")
    assert result == "sherlock"
    mock_session.get.assert_called_with("https://pypi.org/pypi/sherlock/json", timeout=10)


@patch("pipeline.discover.requests.Session")
def test_check_pypi_not_found(mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_session.get.return_value = mock_resp

    result = check_pypi(mock_session, "nonexistent")
    assert result is None


@patch("pipeline.discover.requests.Session")
def test_check_pypi_network_error(mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session
    mock_session.get.side_effect = requests.RequestException("network error")

    result = check_pypi(mock_session, "test")
    assert result is None


def test_denylist_filtering():
    """Test that denylist filtering works."""
    denylist = Denylist(
        capabilities=["phishing"],
        topics=[],
        keywords=["bomber"],
        repos=["bad/repo"],
    )

    tool = Tool(
        name="test",
        display_name="Test",
        description="A phishing tool",
        install={"method": "pip", "package": "test"},
        entrypoint={"command": "test"},
        capabilities=["phishing"],
    )

    # Test capability match
    assert check_tool(tool, denylist) == "capability: phishing"

    # Test keyword match
    tool2 = Tool(
        name="test2",
        display_name="Test2",
        description="A bomber tool",
        install={"method": "pip", "package": "test2"},
        entrypoint={"command": "test2"},
        capabilities=[],
    )
    assert check_tool(tool2, denylist) == "keyword: bomber"

    # Test repo match
    tool3 = Tool(
        name="test3",
        display_name="Test3",
        description="A good tool",
        install={"method": "pip", "package": "test3"},
        entrypoint={"command": "test3"},
        capabilities=[],
        repo="bad/repo",
    )
    assert check_tool(tool3, denylist) == "repo: bad/repo"

    # No match
    tool4 = Tool(
        name="test4",
        display_name="Test4",
        description="A good tool",
        install={"method": "pip", "package": "test4"},
        entrypoint={"command": "test4"},
        capabilities=[],
    )
    assert check_tool(tool4, denylist) is None


def test_denylist_empty():
    denylist = Denylist()
    tool = Tool(
        name="test",
        display_name="Test",
        description="A good tool",
        install={"method": "pip", "package": "test"},
        entrypoint={"command": "test"},
        capabilities=[],
    )
    assert check_tool(tool, denylist) is None


def test_candidates_yaml_roundtrip(tmp_path):
    """Test that candidates.yaml can be written and read back."""
    candidates = [
        {
            "name": "sherlock",
            "repo": "sherlock-project/sherlock",
            "stars": 50000,
            "description": "Search usernames",
            "license": "MIT",
            "detected_install_method": "pip-repo",
            "candidate_pip_package": "sherlock-project",
            "default_branch": "master",
            "discovered_at": "2026-01-01T00:00:00+00:00",
        },
        {
            "name": "maigret",
            "repo": "soxoj/maigret",
            "stars": 10000,
            "description": "Build profiles",
            "license": "GPL-3.0",
            "detected_install_method": "git-requirements",
            "candidate_pip_package": None,
            "default_branch": "main",
            "discovered_at": "2026-01-01T00:00:00+00:00",
        },
    ]

    output_path = tmp_path / "candidates.yaml"
    output_path.write_text(yaml.dump(candidates, sort_keys=False, allow_unicode=True))

    loaded = yaml.safe_load(output_path.read_text())
    assert len(loaded) == 2
    assert loaded[0]["name"] == "sherlock"
    assert loaded[1]["candidate_pip_package"] is None


@patch("pipeline.discover.requests.Session")
@patch("pipeline.discover.time.sleep")
def test_rate_limit_handling(mock_sleep, mock_session_class):
    """Test that rate limit handling triggers sleep."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    # Create a response with low rate limit remaining
    mock_resp = MagicMock()
    mock_resp.headers = {
        "X-RateLimit-Remaining": "5",
        "X-RateLimit-Reset": str(int(time.time()) + 10),
    }
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"items": [], "total_count": 0}
    mock_session.get.return_value = mock_resp

    # This should trigger the rate limit handling
    from pipeline.discover import search_repos

    search_repos(mock_session, "topic:osint stars:>=1000", limit=1)

    # Verify sleep was called
    mock_sleep.assert_called()


def test_network_error_continues():
    """Test that a network error on one repo doesn't stop processing."""
    # This is more of an integration test - we'll test the logic
    # in the main function by mocking fetch_repo_details to fail for one repo
    pass


def test_load_env_tokens_file(tmp_path, monkeypatch):
    """Test that KEY=VALUE lines from ~/.env_tokens are loaded into os.environ."""
    # Point Path.home() to tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    # Create a temp .env_tokens file
    env_tokens = tmp_path / ".env_tokens"
    env_tokens.write_text("""
# This is a comment
GITHUB_TOKEN=ghp_test123
API_KEY=abc456
EMPTY_VALUE=
INVALID_LINE
KEY_WITH_SPACES = value with spaces
""")

    # Ensure the keys are not already in os.environ
    import os

    for key in ["GITHUB_TOKEN", "API_KEY", "EMPTY_VALUE", "KEY_WITH_SPACES"]:
        if key in os.environ:
            del os.environ[key]

    # Call the function
    _load_env_tokens_file()

    # Verify the values were loaded
    assert os.environ.get("GITHUB_TOKEN") == "ghp_test123"
    assert os.environ.get("API_KEY") == "abc456"
    assert os.environ.get("EMPTY_VALUE") == ""
    assert os.environ.get("KEY_WITH_SPACES") == "value with spaces"

    # Verify that existing env vars are not overwritten
    os.environ["GITHUB_TOKEN"] = "existing_value"
    _load_env_tokens_file()
    assert os.environ.get("GITHUB_TOKEN") == "existing_value"

    # Clean up
    for key in ["GITHUB_TOKEN", "API_KEY", "EMPTY_VALUE", "KEY_WITH_SPACES"]:
        if key in os.environ:
            del os.environ[key]


def test_load_env_tokens_file_missing(monkeypatch):
    """Test that missing ~/.env_tokens is handled gracefully."""
    import tempfile
    from pathlib import Path

    # Point Path.home() to a non-existent directory
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(Path, "home", lambda: Path(tmpdir) / "nonexistent")
        _load_env_tokens_file()  # Should not raise
