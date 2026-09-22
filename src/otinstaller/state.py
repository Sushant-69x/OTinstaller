"""Job state persistence: SQLite-backed resume and tracking."""

from __future__ import annotations

import contextlib
import datetime
import sqlite3
from dataclasses import dataclass

from otinstaller.config import get_home, get_state_path


@dataclass(frozen=True)
class InstalledTool:
    name: str
    version: str
    method: str
    source: str
    ref: str | None
    commit: str | None
    entry_command: str | None
    entry_script: str | None
    installed_at: str
    updated_at: str


def _utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    """Open a connection to the state database, running migrations if needed."""
    home = get_home()
    home.mkdir(parents=True, exist_ok=True)
    path = get_state_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """Run database migrations using PRAGMA user_version."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    version = cursor.fetchone()[0]
    if version == 0:
        cursor.execute(
            """
            CREATE TABLE installed (
                name TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                method TEXT NOT NULL,
                source TEXT NOT NULL,
                ref TEXT,
                commit_hash TEXT,
                entry_command TEXT,
                entry_script TEXT,
                installed_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cursor.execute("PRAGMA user_version = 1")
        conn.commit()


def add_installed(tool: InstalledTool) -> None:
    """Insert or replace an installed tool."""
    with contextlib.closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO installed (
                name, version, method, source, ref, commit_hash,
                entry_command, entry_script, installed_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tool.name,
                tool.version,
                tool.method,
                tool.source,
                tool.ref,
                tool.commit,
                tool.entry_command,
                tool.entry_script,
                tool.installed_at,
                tool.updated_at,
            ),
        )
        conn.commit()


def get_installed(name: str) -> InstalledTool | None:
    """Get an installed tool by name."""
    with contextlib.closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM installed WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row is None:
            return None
        return InstalledTool(
            name=row["name"],
            version=row["version"],
            method=row["method"],
            source=row["source"],
            ref=row["ref"],
            commit=row["commit_hash"],
            entry_command=row["entry_command"],
            entry_script=row["entry_script"],
            installed_at=row["installed_at"],
            updated_at=row["updated_at"],
        )


def list_installed() -> list[InstalledTool]:
    """List all installed tools, sorted by name."""
    with contextlib.closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM installed ORDER BY name")
        return [
            InstalledTool(
                name=row["name"],
                version=row["version"],
                method=row["method"],
                source=row["source"],
                ref=row["ref"],
                commit=row["commit_hash"],
                entry_command=row["entry_command"],
                entry_script=row["entry_script"],
                installed_at=row["installed_at"],
                updated_at=row["updated_at"],
            )
            for row in cursor.fetchall()
        ]


def remove_installed(name: str) -> bool:
    """Remove an installed tool by name. Returns True if a row was deleted."""
    with contextlib.closing(connect()) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM installed WHERE name = ?", (name,))
        conn.commit()
        return cursor.rowcount > 0
