"""The contributor report must distinguish field completeness from teaching readiness."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/report_ai_roadmap_readiness.py"


@pytest.fixture
def draft_data(tmp_path):
    data = tmp_path / "data"
    shutil.copytree(ROOT / "docs/learn/ai-roadmap/data", data)
    # Control these optional fields without depending on future author assignments.
    for path in (data / "courses").glob("*.json"):
        course = json.loads(path.read_text(encoding="utf-8"))
        course["instructors"] = []
        course.pop("practice", None)
        course.pop("acceptance", None)
        if course["id"] == "S03":
            course["instructors"] = ["lkeegan"]
            course["practice"] = "Test fixture: implement a bounded function."
            course["acceptance"] = "Test fixture: supplied independent tests pass."
        path.write_text(json.dumps(course), encoding="utf-8")
    return data


def run_report(data, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--data-dir", str(data), *args],
        capture_output=True, text=True, check=False,
    )


def test_report_tracks_gaps_without_certifying_readiness(draft_data):
    result = run_report(draft_data, "--json")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    rows = {row["id"]: row for row in report["courses"]}
    assert len(rows) == 29
    assert rows["A01"]["missing_fields"] == ["instructors", "practice", "acceptance"]
    assert rows["S03"]["missing_fields"] == []
    assert report["missing_counts"] == {"instructors": 28, "practice": 28, "acceptance": 28}
    assert report["teaching_readiness"] == "not_assessed"
    assert "dataset_licensing" in report["manual_review_required"]
    assert "exercise_reproducibility" in report["manual_review_required"]
    assert "four_hour_feasibility" in report["manual_review_required"]


def test_mvp_scope_keeps_both_cli_options(draft_data):
    result = run_report(draft_data, "--mvp", "--json")
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert len(report["courses"]) == 13
    assert all(row["mvp"] for row in report["courses"])
    assert {"S01-C", "S01-O"} <= {row["id"] for row in report["courses"]}
    assert report["missing_counts"] == {"instructors": 12, "practice": 12, "acceptance": 12}


def test_human_report_includes_review_limits(draft_data):
    result = run_report(draft_data, "--mvp")
    assert result.returncode == 0, result.stderr
    assert "13 course options" in result.stdout
    assert "S01-C" in result.stdout and "S01-O" in result.stdout
    assert "Manual review is required for every course" in result.stdout
    assert "Teaching readiness: not assessed" in result.stdout


def test_invalid_curriculum_does_not_produce_a_readiness_report(draft_data):
    (draft_data / "courses/A01.json").unlink()
    result = run_report(draft_data, "--json")
    assert result.returncode == 1
    assert "courses/A01.json" in result.stderr
    assert not result.stdout
