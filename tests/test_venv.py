"""Venv tests."""

import sys

import pytest

from otinstaller.installer.venv import create_venv, venv_bin, venv_python


@pytest.mark.skipif(sys.platform == "win32", reason="venv creation on Windows uses different paths")
def test_create_venv(monkeypatch, tmp_path):
    log = tmp_path / "test.log"
    venv_path = tmp_path / "venv"
    create_venv(venv_path, log)
    python = venv_path / "bin" / "python"
    assert python.exists()


def test_venv_python(monkeypatch, tmp_path):
    root = tmp_path / "tool"
    venv_dir = root / "venv"
    venv_dir.mkdir(parents=True)
    (venv_dir / "bin").mkdir()
    (venv_dir / "bin" / "python").write_text("#!/bin/sh\necho test")
    (venv_dir / "bin" / "python").chmod(0o755)
    assert venv_python(root) == venv_dir / "bin" / "python"


def test_venv_bin(monkeypatch, tmp_path):
    root = tmp_path / "tool"
    venv_dir = root / "venv"
    venv_dir.mkdir(parents=True)
    (venv_dir / "bin").mkdir()
    (venv_dir / "bin" / "myscript").write_text("#!/bin/sh\necho test")
    (venv_dir / "bin" / "myscript").chmod(0o755)
    assert venv_bin(root, "myscript") == venv_dir / "bin" / "myscript"
