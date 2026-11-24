"""Root-level commands must discover the prebuilt-site option before collecting tests."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("equals", [False, True])
def test_root_discovery_accepts_prebuilt_site_option(equals):
    # Discovery needs no build. Use an existing directory to exercise pytest's path inference.
    option = ["--roadmap-site-dir=docs"] if equals else ["--roadmap-site-dir", "docs"]
    result = collect_from_root(option)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_every_course_dialog" in result.stdout


def test_root_discovery_accepts_external_build_with_equals(tmp_path):
    result = collect_from_root([f"--roadmap-site-dir={tmp_path}"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_every_course_dialog" in result.stdout


def collect_from_root(option):
    environment = os.environ.copy()
    environment.pop("PYTEST_ADDOPTS", None)
    return subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-m", "browser", *option],
        cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30, check=False,
    )
