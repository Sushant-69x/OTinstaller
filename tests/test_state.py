"""State tests."""

from otinstaller.state import (
    InstalledTool,
    add_installed,
    connect,
    get_installed,
    list_installed,
    remove_installed,
)


def test_migration_sets_user_version(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    assert cursor.fetchone()[0] == 1
    conn.close()


def test_add_and_get_installed(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    tool = InstalledTool(
        name="test",
        version="1.0",
        method="pip",
        source="test-pkg",
        ref=None,
        commit=None,
        entry_command="test",
        entry_script=None,
        installed_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-01T00:00:00+00:00",
    )
    add_installed(tool)
    got = get_installed("test")
    assert got == tool


def test_add_replace_installed(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    tool1 = InstalledTool(
        name="test",
        version="1.0",
        method="pip",
        source="test-pkg",
        ref=None,
        commit=None,
        entry_command="test",
        entry_script=None,
        installed_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-01T00:00:00+00:00",
    )
    tool2 = InstalledTool(
        name="test",
        version="2.0",
        method="pip",
        source="test-pkg",
        ref=None,
        commit=None,
        entry_command="test",
        entry_script=None,
        installed_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-02T00:00:00+00:00",
    )
    add_installed(tool1)
    add_installed(tool2)
    got = get_installed("test")
    assert got.version == "2.0"


def test_list_installed_sorted(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    for name in ["ztool", "atool", "mtool"]:
        tool = InstalledTool(
            name=name,
            version="1.0",
            method="pip",
            source="pkg",
            ref=None,
            commit=None,
            entry_command=name,
            entry_script=None,
            installed_at="2024-01-01T00:00:00+00:00",
            updated_at="2024-01-01T00:00:00+00:00",
        )
        add_installed(tool)
    tools = list_installed()
    assert [t.name for t in tools] == ["atool", "mtool", "ztool"]


def test_remove_installed(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    tool = InstalledTool(
        name="test",
        version="1.0",
        method="pip",
        source="test-pkg",
        ref=None,
        commit=None,
        entry_command="test",
        entry_script=None,
        installed_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-01T00:00:00+00:00",
    )
    add_installed(tool)
    assert remove_installed("test") is True
    assert get_installed("test") is None
    assert remove_installed("test") is False


def test_sql_injection_safe(monkeypatch, tmp_path):
    """Test that names with quotes and SQL text are stored as plain data."""
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    name = "test'; DROP TABLE installed; --"
    tool = InstalledTool(
        name=name,
        version="1.0",
        method="pip",
        source="pkg",
        ref=None,
        commit=None,
        entry_command="cmd",
        entry_script=None,
        installed_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-01T00:00:00+00:00",
    )
    add_installed(tool)
    got = get_installed(name)
    assert got is not None
    assert got.name == name
