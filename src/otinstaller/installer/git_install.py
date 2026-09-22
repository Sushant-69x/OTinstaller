"""Git-based installation."""

from __future__ import annotations

import shutil
from pathlib import Path

from otinstaller.installer.process import InstallError, run, run_capture
from otinstaller.installer.venv import create_venv, venv_python
from otinstaller.registry import Tool


def install_git(
    tool: Tool,
    root: Path,
    log: Path,
    stream: bool = False,
) -> str:
    """Install a tool from a git repository. Returns the commit hash."""
    if shutil.which("git") is None:
        raise InstallError("git is not installed")

    url = tool.install.url
    if not url:
        raise InstallError("git install requires a URL")

    if url.startswith("-"):
        raise InstallError(f"refusing to use URL starting with '-': {url}")

    src_dir = root / "src"
    ref = tool.install.ref

    if ref and ref.startswith("-"):
        raise InstallError(f"refusing to use ref starting with '-': {ref}")

    # Validate requirements path before cloning to avoid network activity on invalid paths
    if tool.install.requirements:
        req_path = Path(tool.install.requirements)
        # Check for path traversal attempts before any network activity
        try:
            if req_path.is_absolute() or ".." in req_path.parts:
                raise InstallError(f"requirements path escapes clone: {tool.install.requirements}")
        except OSError:
            raise InstallError(
                f"requirements path escapes clone: {tool.install.requirements}"
            ) from None

    # Clone
    if ref is None:
        run(
            ["git", "clone", "--depth", "1", "--", url, str(src_dir)],
            log=log,
            stream=stream,
        )
    else:
        run(
            ["git", "clone", "--", url, str(src_dir)],
            log=log,
            stream=stream,
        )
        run(
            ["git", "-C", str(src_dir), "checkout", ref],
            log=log,
            stream=stream,
        )

    # Create venv
    venv_dir = root / "venv"
    create_venv(venv_dir, log, stream=stream)

    python = venv_python(root)

    if tool.install.requirements:
        req_path = src_dir / tool.install.requirements
        # Resolve and check it's inside the clone
        try:
            resolved_req = req_path.resolve()
            resolved_src = src_dir.resolve()
            if not str(resolved_req).startswith(str(resolved_src)):
                raise InstallError(f"requirements path escapes clone: {tool.install.requirements}")
        except OSError as e:
            raise InstallError(f"requirements path not found: {tool.install.requirements}") from e
        if not req_path.is_file():
            raise InstallError(f"requirements path not found: {tool.install.requirements}")
        run(
            [str(python), "-m", "pip", "install", "-r", str(req_path)],
            log=log,
            stream=stream,
        )

    if tool.install.as_package:
        run(
            [str(python), "-m", "pip", "install", str(src_dir)],
            log=log,
            stream=stream,
        )

    # Get commit hash
    commit = run_capture(["git", "-C", str(src_dir), "rev-parse", "HEAD"], cwd=src_dir)
    return commit
