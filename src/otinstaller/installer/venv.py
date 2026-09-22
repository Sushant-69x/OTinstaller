"""Virtual environment utilities."""

from __future__ import annotations

import sys
from pathlib import Path

from otinstaller.installer.process import run


def create_venv(path: Path, log: Path, stream: bool = False) -> None:
    """Create a virtual environment at the given path."""
    run(
        [sys.executable, "-m", "venv", str(path)],
        log=log,
        stream=stream,
    )


def venv_python(root: Path) -> Path:
    """Return the path to the Python executable in the venv."""
    return root / "venv" / "bin" / "python"


def venv_bin(root: Path, name: str) -> Path:
    """Return the path to a binary in the venv's bin directory."""
    return root / "venv" / "bin" / name
