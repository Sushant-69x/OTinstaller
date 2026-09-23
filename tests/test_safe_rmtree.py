"""Safe rmtree tests."""

import pytest

from otinstaller.config import get_tools_dir
from otinstaller.installer.core import InstallError, safe_rmtree


def test_safe_rmtree_deletes_normal_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    target = get_tools_dir() / "testtool"
    target.mkdir(parents=True)
    (target / "file.txt").write_text("content")
    safe_rmtree(target)
    assert not target.exists()


def test_safe_rmtree_refuses_outside_tools_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "file.txt").write_text("content")
    with pytest.raises(InstallError, match="refusing to remove path outside tools directory"):
        safe_rmtree(outside)


def test_safe_rmtree_refuses_tools_dir_itself(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    tools = get_tools_dir()
    tools.mkdir(parents=True)
    with pytest.raises(InstallError, match="refusing to remove tools directory"):
        safe_rmtree(tools)


def test_safe_rmtree_refuses_dotdot_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    # Try to pass a path that resolves to outside the tools directory
    bad_path = tmp_path / "outside"
    bad_path.mkdir()
    with pytest.raises(InstallError, match="refusing to remove path outside tools directory"):
        safe_rmtree(bad_path)


def test_safe_rmtree_unlinks_symlink(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    target = get_tools_dir() / "testtool"
    target.mkdir(parents=True)
    link = get_tools_dir() / "linktool"
    link.symlink_to(target)
    assert link.is_symlink()
    safe_rmtree(link)
    assert not link.exists()
    assert target.exists()  # target should be untouched
