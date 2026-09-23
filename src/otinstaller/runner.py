"""Tool execution: running tools in their virtualenvs and capturing output."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from otinstaller.config import get_results_dir
from otinstaller.installer.venv import venv_bin, venv_python
from otinstaller.registry import Tool
from otinstaller.results import RunMeta, hash_file, results_paths, write_meta


def build_command(tool: Tool, root: Path, extra_args: list[str]) -> list[str]:
    """Build the command to run a tool."""
    if tool.entrypoint.command:
        return [str(venv_bin(root, tool.entrypoint.command)), *extra_args]
    elif tool.entrypoint.script:
        return [str(venv_python(root)), str(root / "src" / tool.entrypoint.script), *extra_args]
    else:
        raise ValueError(f"tool {tool.name} has no entrypoint")


def _redact_api_keys(command: list[str], tool: Tool) -> list[str]:
    """Redact API key values from command for meta file."""
    # API keys are passed via environment, not command line, but just in case
    redacted = []
    for arg in command:
        key_names = tool.api_keys.required + tool.api_keys.optional
        if any(arg.startswith(f"{key}=") for key in key_names):
            redacted.append("***")
        else:
            redacted.append(arg)
    return redacted


def run_tool(
    tool: Tool,
    root: Path,
    extra_args: list[str],
    *,
    target: str | None,
    case: str | None,
    env_overrides: dict[str, str] | None,
    stream: bool,
) -> RunMeta:
    """Run a tool and return RunMeta. Does not raise on tool exit code."""
    # Determine target
    if target is None:
        target = extra_args[0] if extra_args else "unspecified"

    output_path, meta_path = results_paths(tool.name, target, case)

    # Build command
    cmd = build_command(tool, root, extra_args)

    # Prepare environment
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    # Start timing
    started_at = datetime.now(timezone.utc)
    started_at_str = started_at.isoformat()

    # Open output file for writing
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run the process in its own process group
    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    # Stream output to file (and terminal if stream=True)
    with output_path.open("wb") as f:
        if proc.stdout:
            for line in iter(proc.stdout.readline, b""):
                f.write(line)
                if stream:
                    sys.stdout.buffer.write(line)
                    sys.stdout.buffer.flush()

    # Wait for process to complete
    exit_code = proc.wait()
    ended_at = datetime.now(timezone.utc)
    ended_at_str = ended_at.isoformat()
    duration = (ended_at - started_at).total_seconds()

    # Determine status
    if exit_code == 0:
        status = "complete"
    elif exit_code < 0:
        # Negative exit code means killed by signal
        status = "interrupted"
    else:
        status = "failed"

    # Hash the output file
    sha256 = hash_file(output_path)
    bytes_size = output_path.stat().st_size

    # Build meta
    redacted_cmd = _redact_api_keys(cmd, tool)
    meta = RunMeta(
        command=redacted_cmd,
        tool=tool.name,
        tool_version="",  # Will be filled by caller
        target=target,
        case=case,
        started_at=started_at_str,
        ended_at=ended_at_str,
        duration_seconds=duration,
        exit_code=exit_code,
        status=status,
        output_path=str(output_path.relative_to(get_results_dir())),
        sha256=sha256,
        bytes=bytes_size,
    )

    write_meta(meta, meta_path)
    return meta
