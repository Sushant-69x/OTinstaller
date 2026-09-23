"""Config tests."""

from pathlib import Path

from otinstaller.config import (
    ensure_dir,
    get_accept_path,
    get_distro,
    get_distro_family,
    get_env_file,
    get_home,
    get_logs_dir,
    get_results_dir,
    get_state_path,
    get_tools_dir,
    tool_dir,
)


def test_get_home_default(monkeypatch):
    monkeypatch.delenv("OTINSTALLER_HOME", raising=False)
    home = get_home()
    assert str(home).endswith(".otinstaller")


def test_get_home_env(monkeypatch, tmp_path):
    custom = tmp_path / "custom_home"
    monkeypatch.setenv("OTINSTALLER_HOME", str(custom))
    home = get_home()
    assert home == custom


def test_get_results_dir_default(monkeypatch):
    monkeypatch.delenv("OTINSTALLER_RESULTS_DIR", raising=False)
    results = get_results_dir()
    assert results == Path.cwd() / "results"


def test_get_results_dir_env(monkeypatch, tmp_path):
    custom = tmp_path / "custom_results"
    monkeypatch.setenv("OTINSTALLER_RESULTS_DIR", str(custom))
    results = get_results_dir()
    assert results == custom


def test_get_env_file():
    env_file = get_env_file()
    assert env_file == get_home() / ".env"


def test_ensure_dir_creates_nested(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    result = ensure_dir(nested)
    assert result == nested
    assert nested.exists()
    assert nested.is_dir()


def test_ensure_dir_idempotent(tmp_path):
    dir_path = tmp_path / "testdir"
    ensure_dir(dir_path)
    result = ensure_dir(dir_path)
    assert result == dir_path
    assert dir_path.exists()


def test_get_tools_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    assert get_tools_dir() == tmp_path / "tools"


def test_get_logs_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    assert get_logs_dir() == tmp_path / "logs"


def test_get_state_path(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    assert get_state_path() == tmp_path / "state.db"


def test_get_accept_path(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    assert get_accept_path() == tmp_path / "accepted.json"


def test_tool_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("OTINSTALLER_HOME", str(tmp_path))
    assert tool_dir("sherlock") == tmp_path / "tools" / "sherlock"


def test_get_distro_ubuntu(monkeypatch, tmp_path):
    os_release = tmp_path / "os-release"
    os_release.write_text('ID="ubuntu"\nVERSION_ID="24.04"\n')
    monkeypatch.setattr(
        "otinstaller.config.Path", lambda x: os_release if x == "/etc/os-release" else Path(x)
    )
    assert get_distro() == "ubuntu"


def test_get_distro_debian(monkeypatch, tmp_path):
    os_release = tmp_path / "os-release"
    os_release.write_text('ID="debian"\nVERSION_ID="12"\n')
    monkeypatch.setattr(
        "otinstaller.config.Path", lambda x: os_release if x == "/etc/os-release" else Path(x)
    )
    assert get_distro() == "debian"


def test_get_distro_arch(monkeypatch, tmp_path):
    os_release = tmp_path / "os-release"
    os_release.write_text('ID="arch"\n')
    monkeypatch.setattr(
        "otinstaller.config.Path", lambda x: os_release if x == "/etc/os-release" else Path(x)
    )
    assert get_distro() == "arch"


def test_get_distro_kali(monkeypatch, tmp_path):
    os_release = tmp_path / "os-release"
    os_release.write_text('ID="kali"\nID_LIKE="debian"\n')
    monkeypatch.setattr(
        "otinstaller.config.Path", lambda x: os_release if x == "/etc/os-release" else Path(x)
    )
    assert get_distro() == "kali"


def test_get_distro_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "otinstaller.config.Path",
        lambda x: tmp_path / "nonexistent" if x == "/etc/os-release" else Path(x),
    )
    assert get_distro() == "unknown"


def test_get_distro_family_debian(monkeypatch, tmp_path):
    os_release = tmp_path / "os-release"
    os_release.write_text('ID="ubuntu"\n')
    monkeypatch.setattr(
        "otinstaller.config.Path", lambda x: os_release if x == "/etc/os-release" else Path(x)
    )
    assert get_distro_family() == "debian"


def test_get_distro_family_debian_from_id_like(monkeypatch, tmp_path):
    os_release = tmp_path / "os-release"
    os_release.write_text('ID="linuxmint"\nID_LIKE="ubuntu debian"\n')
    monkeypatch.setattr(
        "otinstaller.config.Path", lambda x: os_release if x == "/etc/os-release" else Path(x)
    )
    assert get_distro_family() == "debian"


def test_get_distro_family_arch(monkeypatch, tmp_path):
    os_release = tmp_path / "os-release"
    os_release.write_text('ID="manjaro"\n')
    monkeypatch.setattr(
        "otinstaller.config.Path", lambda x: os_release if x == "/etc/os-release" else Path(x)
    )
    assert get_distro_family() == "arch"


def test_get_distro_family_arch_from_id_like(monkeypatch, tmp_path):
    os_release = tmp_path / "os-release"
    os_release.write_text('ID="endeavouros"\nID_LIKE="arch"\n')
    monkeypatch.setattr(
        "otinstaller.config.Path", lambda x: os_release if x == "/etc/os-release" else Path(x)
    )
    assert get_distro_family() == "arch"


def test_get_distro_family_unknown(monkeypatch, tmp_path):
    os_release = tmp_path / "os-release"
    os_release.write_text('ID="fedora"\n')
    monkeypatch.setattr(
        "otinstaller.config.Path", lambda x: os_release if x == "/etc/os-release" else Path(x)
    )
    assert get_distro_family() == "unknown"


def test_get_distro_family_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "otinstaller.config.Path",
        lambda x: tmp_path / "nonexistent" if x == "/etc/os-release" else Path(x),
    )
    assert get_distro_family() == "unknown"
