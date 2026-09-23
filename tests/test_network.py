"""Network tests (require RUN_NETWORK_TESTS=1)."""

import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time

import pytest
from typer.testing import CliRunner

from otinstaller.cli import app

runner = CliRunner()

# Only run if RUN_NETWORK_TESTS=1 is set
pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_NETWORK_TESTS"),
    reason="Network tests require RUN_NETWORK_TESTS=1",
)


@pytest.mark.network
def test_network_install_sherlock():
    """Install sherlock into a temporary OTINSTALLER_HOME and remove it."""
    with tempfile.TemporaryDirectory() as tmp_home:
        os.environ["OTINSTALLER_HOME"] = tmp_home

        # Init
        result = runner.invoke(app, ["init", "--yes"])
        assert result.exit_code == 0

        # Install sherlock
        result = runner.invoke(app, ["install", "sherlock", "--yes"])
        assert result.exit_code == 0
        assert "installed sherlock" in result.output

        # Verify it's installed
        result = runner.invoke(app, ["list", "--installed"])
        assert result.exit_code == 0
        assert "sherlock" in result.output

        # Run sherlock --help
        sherlock_bin = os.path.join(tmp_home, "tools", "sherlock", "venv", "bin", "sherlock")
        assert os.path.exists(sherlock_bin)

        # Remove sherlock
        result = runner.invoke(app, ["remove", "sherlock", "--yes"])
        assert result.exit_code == 0
        assert "removed sherlock" in result.output

        # Verify it's removed
        result = runner.invoke(app, ["list", "--installed"])
        assert result.exit_code == 0
        assert "no tools installed" in result.output or "sherlock" not in result.output


@pytest.mark.network
def test_network_sigint_cleanup():
    """SIGINT during install cleans up tool directory and database row."""
    with tempfile.TemporaryDirectory() as tmp_home:
        os.environ["OTINSTALLER_HOME"] = tmp_home

        # Init first
        result = runner.invoke(app, ["init", "--yes"])
        assert result.exit_code == 0

        # Start install in background using subprocess in its own process group
        # so we can send SIGINT to it without affecting the test process
        otinstaller_path = shutil.which("otinstaller") or [sys.executable, "-m", "otinstaller"]
        if isinstance(otinstaller_path, str):
            otinstaller_path = [otinstaller_path]
        proc = subprocess.Popen(
            [
                *otinstaller_path,
                "install",
                "maigret",
                "--yes",
            ],
            env={**os.environ, "OTINSTALLER_HOME": tmp_home},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )

        # Wait for install to start (pip install phase)
        time.sleep(3)

        # Send SIGINT to the child process group only
        os.killpg(os.getpgid(proc.pid), signal.SIGINT)

        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            proc.wait(timeout=5)

        # Verify tool directory is cleaned up
        maigret_dir = os.path.join(tmp_home, "tools", "maigret")
        assert not os.path.exists(maigret_dir), f"Directory {maigret_dir} should be cleaned up"

        # Verify no database row exists
        from otinstaller.state import connect

        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM installed WHERE name = 'maigret'")
        row = cursor.fetchone()
        conn.close()
        assert row is None, "Database row should not exist after SIGINT cleanup"
