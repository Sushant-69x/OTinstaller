"""Denylist tests."""

from pathlib import Path

import pytest
import yaml

from otinstaller.denylist import Denylist, check_tool, filter_tools, load_denylist
from otinstaller.registry import Entrypoint, Install, RegistryError, Tool


def make_tool(**kwargs) -> Tool:
    defaults = {
        "name": "testtool",
        "display_name": "Test Tool",
        "description": "A test tool",
        "install": Install(method="pip", package="testtool"),
        "entrypoint": Entrypoint(command="testtool"),
    }
    defaults.update(kwargs)
    return Tool(**defaults)


def test_load_denylist_missing_file():
    denylist = load_denylist(Path("/nonexistent/path.yaml"))
    assert denylist == Denylist()


def test_load_denylist_empty():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({}, f)
        f.flush()
        denylist = load_denylist(Path(f.name))
        assert denylist == Denylist()


def test_load_denylist_missing_keys_count_as_empty():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"capabilities": ["phishing"]}, f)
        f.flush()
        denylist = load_denylist(Path(f.name))
        assert denylist.capabilities == ("phishing",)
        assert denylist.topics == ()
        assert denylist.keywords == ()
        assert denylist.repos == ()


def test_load_denylist_wrong_type_raises():
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"capabilities": "not a list"}, f)
        f.flush()
        with pytest.raises(RegistryError, match="denylist.capabilities must be a list"):
            load_denylist(Path(f.name))


def test_check_tool_capability_denied():
    denylist = Denylist(capabilities=("phishing",))
    tool = make_tool(capabilities=("phishing", "username-search"))
    assert check_tool(tool, denylist) == "capability: phishing"


def test_check_tool_topic_denied():
    denylist = Denylist(topics=("malware",))
    tool = make_tool(topics=("recon", "malware"))
    assert check_tool(tool, denylist) == "topic: malware"


def test_check_tool_keyword_denied():
    denylist = Denylist(keywords=("phishing",))
    tool = make_tool(name="mytool", description="A phishing tool")
    assert check_tool(tool, denylist) == "keyword: phishing"


def test_check_tool_keyword_case_insensitive():
    denylist = Denylist(keywords=("PHISHING",))
    tool = make_tool(name="mytool", description="A Phishing tool")
    assert check_tool(tool, denylist) == "keyword: PHISHING"


def test_check_tool_repo_denied():
    denylist = Denylist(repos=("bad/repo",))
    tool = make_tool(repo="bad/repo")
    assert check_tool(tool, denylist) == "repo: bad/repo"


def test_check_tool_repo_case_insensitive():
    denylist = Denylist(repos=("BAD/REPO",))
    tool = make_tool(repo="bad/repo")
    assert check_tool(tool, denylist) == "repo: BAD/REPO"


def test_check_tool_allowed():
    denylist = Denylist(
        capabilities=("phishing",),
        topics=("malware",),
        keywords=("bad",),
        repos=("bad/repo",),
    )
    tool = make_tool(
        capabilities=("username-search",),
        topics=("recon",),
        name="goodtool",
        description="A good tool",
        repo="good/repo",
    )
    assert check_tool(tool, denylist) is None


def test_filter_tools_splits_correctly():
    denylist = Denylist(capabilities=("phishing",))
    tool_allowed = make_tool(name="allowed", capabilities=("username-search",))
    tool_denied = make_tool(name="denied", capabilities=("phishing",))
    allowed, denied = filter_tools([tool_allowed, tool_denied], denylist)
    assert allowed == [tool_allowed]
    assert denied == [(tool_denied, "capability: phishing")]
