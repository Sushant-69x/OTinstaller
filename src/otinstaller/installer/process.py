"""Process execution utilities."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


class InstallError(Exception):
    """Raised when installation fails."""

    pass


def _base_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PIP_NO_INPUT"] = "1"
    return env


def run(
    args: list[str],
    *,
    log: Path,
    cwd: Path | None = None,
    timeout: int = 900,
    stream: bool = False,
) -> None:
    """Run a command, logging output to a file."""
    cmd_str = " ".join(args)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8", errors="replace") as f:
        f.write(f"$ {cmd_str}\n")
    env = _base_env()
    try:
        if stream:
            subprocess.run(
                args,
                cwd=cwd,
                timeout=timeout,
                check=True,
                env=env,
            )
        else:
            result = subprocess.run(
                args,
                cwd=cwd,
                timeout=timeout,
                capture_output=True,
                text=True,
                env=env,
            )
            with log.open("a", encoding="utf-8", errors="replace") as f:
                f.write(result.stdout or "")
                f.write(result.stderr or "")
            if result.returncode != 0:
                _raise_from_log(args[0], log)
    except subprocess.TimeoutExpired as e:
        raise InstallError(f"timed out after {timeout} seconds: {args[0]}") from e


def run_capture(
    args: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 60,
) -> str:
    """Run a command and return stdout, raising on failure."""
    env = _base_env()
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise InstallError(f"{args[0]} failed: {e.stderr.strip() or e.stdout.strip()}") from e
    except subprocess.TimeoutExpired as e:
        raise InstallError(f"timed out after {timeout} seconds: {args[0]}") from e


def _raise_from_log(cmd_name: str, log: Path) -> None:
    """Read the last 15 lines of the log and raise InstallError."""
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = "\n".join(lines[-15:])
    raise InstallError(f"{cmd_name} failed:\n{tail}\nlog: {log}")
