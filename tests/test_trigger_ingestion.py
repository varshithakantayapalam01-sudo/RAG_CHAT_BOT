from __future__ import annotations

"""
Unit & Integration Tests for Ingestion Orchestrator (scripts/trigger_ingestion.py)

Validates sequential execution of download, extraction, and ingestion scripts,
error propagation, and custom argument forwarding.
"""

import subprocess
import sys
from pathlib import Path
import pytest

# Ensure scripts directory can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import trigger_ingestion


class DummyCompletedProcess:
    def __init__(self, returncode: int = 0):
        self.returncode = returncode


def test_trigger_ingestion_success(monkeypatch) -> None:
    """Test that main() calls all three ingestion pipeline scripts sequentially and returns 0."""
    executed_commands = []

    def mock_run(cmd, cwd=None, **kwargs):
        executed_commands.append(cmd)
        return DummyCompletedProcess(0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    exit_code = trigger_ingestion.main()
    assert exit_code == 0
    assert len(executed_commands) == 3

    # Verify order of execution
    assert "download_sources.py" in str(executed_commands[0][1])
    assert "extract_text.py" in str(executed_commands[1][1])
    assert "run_ingestion.py" in str(executed_commands[2][1])
    assert "--clean" in executed_commands[2]


def test_trigger_ingestion_custom_args(monkeypatch) -> None:
    """Test that custom arguments passed to main() are forwarded to run_ingestion.py."""
    executed_commands = []

    def mock_run(cmd, cwd=None, **kwargs):
        executed_commands.append(cmd)
        return DummyCompletedProcess(0)

    monkeypatch.setattr(subprocess, "run", mock_run)

    exit_code = trigger_ingestion.main(["--mode", "text"])
    assert exit_code == 0
    assert "--mode" in executed_commands[2]
    assert "text" in executed_commands[2]


def test_trigger_ingestion_step_failure(monkeypatch) -> None:
    """Test that if a step fails, SystemExit is raised with the failing return code."""
    def mock_run_fail(cmd, cwd=None, **kwargs):
        if "extract_text.py" in str(cmd[1]):
            return DummyCompletedProcess(2)
        return DummyCompletedProcess(0)

    monkeypatch.setattr(subprocess, "run", mock_run_fail)

    with pytest.raises(SystemExit) as exc_info:
        trigger_ingestion.main()
    assert exc_info.value.code == 2


def test_run_script_missing_script(monkeypatch, tmp_path) -> None:
    """Test that run_script exits with code 1 if the target script file does not exist."""
    monkeypatch.setattr(trigger_ingestion, "PROJECT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        trigger_ingestion.run_script("nonexistent_script.py")
    assert exc_info.value.code == 1
