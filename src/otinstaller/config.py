"""Configuration helpers."""

import os
from pathlib import Path


def get_distro() -> str:
    """Return the distro ID from /etc/os-release (lowercased), or 'unknown'."""
    path = Path("/etc/os-release")
    if not path.exists():
        return "unknown"
    try:
        content = path.read_text()
        for line in content.splitlines():
            if line.startswith("ID="):
                value = line.split("=", 1)[1].strip().strip('"')
                return value.lower()
    except Exception:
        pass
    return "unknown"


def get_distro_family() -> str:
    """Return the distro family: 'debian', 'arch', or 'unknown'."""
    distro = get_distro()
    if distro in ("ubuntu", "debian", "kali", "linuxmint", "pop", "elementary", "zorin"):
        return "debian"
    if distro in ("arch", "manjaro", "endeavouros", "garuda", "artix"):
        return "arch"
    # Check ID_LIKE for derivatives
    path = Path("/etc/os-release")
    if path.exists():
        try:
            content = path.read_text()
            for line in content.splitlines():
                if line.startswith("ID_LIKE="):
                    value = line.split("=", 1)[1].strip().strip('"').lower()
                    if "debian" in value or "ubuntu" in value:
                        return "debian"
                    if "arch" in value:
                        return "arch"
        except Exception:
            pass
    return "unknown"


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
