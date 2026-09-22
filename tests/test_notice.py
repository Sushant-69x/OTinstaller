"""Notice tests."""

import json
import sys

import pytest

from otinstaller.config import get_accept_path
from otinstaller.notice import has_accepted, record_acceptance


def test_not_accepted_initially(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    assert has_accepted() is False


def test_accepted_after_record(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    record_acceptance()
    assert has_accepted() is True


def test_wrong_version_not_accepted(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    path = get_accept_path()
    path.write_text(json.dumps({"version": "0", "accepted_at": "2024-01-01T00:00:00+00:00"}))
    assert has_accepted() is False


def test_corrupt_file_not_accepted(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    path = get_accept_path()
    path.write_text("not json")
    assert has_accepted() is False


@pytest.mark.skipif(sys.platform == "win32", reason="file permissions work differently on Windows")
def test_accept_file_mode_600(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    record_acceptance()
    path = get_accept_path()
    mode = path.stat().st_mode & 0o777
    assert mode == 0o600
