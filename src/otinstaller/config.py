"""Configuration helpers."""

import os
from pathlib import Path


def get_home() -> Path:
    """Return the otinstaller home directory."""
    env_home = os.environ.get("OTINSTALLER_HOME")
    if env_home:
        return Path(env_home).expanduser()
    return Path.home() / ".otinstaller"


def get_results_dir() -> Path:
    """Return the results directory."""
    env_results = os.environ.get("OTINSTALLER_RESULTS_DIR")
    if env_results:
        return Path(env_results).expanduser()
    return Path.cwd() / "results"


def get_env_file() -> Path:
    """Return the path to the .env file."""
    return get_home() / ".env"


def ensure_dir(path: Path) -> Path:
    """Create directory and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_tools_dir() -> Path:
    """Return the tools directory."""
    return get_home() / "tools"


def get_logs_dir() -> Path:
    """Return the logs directory."""
    return get_home() / "logs"


def get_state_path() -> Path:
    """Return the path to the state database."""
    return get_home() / "state.db"


def get_accept_path() -> Path:
    """Return the path to the acceptance file."""
    return get_home() / "accepted.json"


def tool_dir(name: str) -> Path:
    """Return the directory for a specific tool."""
    return get_tools_dir() / name
