"""Regression coverage for malformed public curriculum data."""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "validate_ai_roadmap", ROOT / "scripts/validate_ai_roadmap.py"
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


@pytest.fixture
def curriculum(tmp_path):
    data = tmp_path / "data"
    shutil.copytree(ROOT / "docs/learn/ai-roadmap/data", data)
    return data


def edit(data, filename, change):
    path = data / filename
    value = json.loads(path.read_text(encoding="utf-8"))
    change(value)
    path.write_text(json.dumps(value), encoding="utf-8")


def rejects(data, message):
    with pytest.raises(ValueError, match=message):
        validator.validate_curriculum(data)


def test_public_curriculum():
    validator.validate_curriculum()


@pytest.mark.parametrize("field", ["learn", "tools", "modules", "moduleDescriptions", "roles", "references"])
def test_reject_empty_required_lists(curriculum, field):
    edit(curriculum, "courses/A01.json", lambda c: c.update({field: []}))
    rejects(curriculum, "courses/A01.json")


@pytest.mark.parametrize("field", ["name", "outcome", "description", "prerequisiteRationale"])
def test_reject_blank_required_text(curriculum, field):
    edit(curriculum, "courses/A01.json", lambda c: c.update({field: "   "}))
    rejects(curriculum, "courses/A01.json")


@pytest.mark.parametrize("field", ["goal", "roles", "references", "instructors"])
def test_reject_unknown_course_references(curriculum, field):
    value = "unknown" if field == "goal" else ["unknown"]
    edit(curriculum, "courses/A01.json", lambda c: c.update({field: value}))
    rejects(curriculum, "courses/A01.json")


@pytest.mark.parametrize("duration", [0, 241, "240"])
def test_reject_invalid_durations(curriculum, duration):
    edit(curriculum, "courses/A01.json", lambda c: c.update(duration_minutes=duration))
    rejects(curriculum, "duration_minutes")


def test_reject_missing_required_field(curriculum):
    edit(curriculum, "courses/A01.json", lambda c: c.pop("outcome"))
    rejects(curriculum, "courses/A01.json")


def test_reject_misaligned_module_descriptions(curriculum):
    edit(curriculum, "courses/A01.json", lambda c: c["moduleDescriptions"].pop())
    rejects(curriculum, "moduleDescriptions")


def test_reject_project_without_acceptance(curriculum):
    edit(curriculum, "courses/S01-C.json", lambda c: c.pop("acceptance"))
    rejects(curriculum, "acceptance")


def test_unassigned_instructors_are_valid(curriculum):
    edit(curriculum, "courses/S03.json", lambda c: c.update(instructors=[]))
    validator.validate_curriculum(curriculum)


@pytest.mark.parametrize("filename,change", [
    ("roadmap.json", lambda d: d["course_ids"].append("A01")),
    ("audiences.json", lambda d: d["students"].pop("help")),
    ("learning-goals.json", lambda d: d.update({"LG-01": " "})),
    ("instructors.json", lambda d: d["lkeegan"].pop("affiliation")),
    ("instructors.json", lambda d: d["lkeegan"].update(github="javascript:alert(1)")),
    ("bibliography.json", lambda d: d["nist"].pop("citation")),
    ("layout.json", lambda d: d.update(elements="invalid")),
    ("layout.json", lambda d: d["svg"].update(width="not-a-number")),
])
def test_reject_malformed_shared_records(curriculum, filename, change):
    edit(curriculum, filename, change)
    rejects(curriculum, filename)


@pytest.mark.parametrize("filename,change", [
    ("courses/A01.json", lambda d: d.update(tutor_notes="private")),
    ("instructors.json", lambda d: d["lkeegan"].update(private_email="private")),
    ("bibliography.json", lambda d: d["nist"].update(internal_source="private")),
    ("audiences.json", lambda d: d["students"].update(internal_notes="private")),
    ("dependencies.json", lambda d: d["A01"].update(tutor_notes="private")),
    ("layout.json", lambda d: d["elements"][0].update(tutor_notes="private")),
])
def test_reject_nonpublic_fields(curriculum, filename, change):
    edit(curriculum, filename, change)
    rejects(curriculum, filename)


@pytest.mark.parametrize("filename", ["tutor.json", "internal/notes.md", "courses/PRIVATE.json"])
def test_reject_unlisted_public_data_files(curriculum, filename):
    path = curriculum / filename
    path.parent.mkdir(exist_ok=True)
    path.write_text("{}", encoding="utf-8")
    rejects(curriculum, "Unexpected public data files")


def test_reject_missing_course_file(curriculum):
    (curriculum / "courses/A01.json").unlink()
    rejects(curriculum, "courses/A01.json")


def test_reject_duplicate_json_keys(curriculum):
    (curriculum / "instructors.json").write_text('{"lkeegan": {}, "lkeegan": {}}', encoding="utf-8")
    rejects(curriculum, "instructors.json.*Duplicate JSON key")


def test_reject_invalid_json(curriculum):
    (curriculum / "roadmap.json").write_text("{", encoding="utf-8")
    rejects(curriculum, "roadmap.json")


def test_reject_course_id_mismatch(curriculum):
    edit(curriculum, "courses/A01.json", lambda d: d.update(id="A02"))
    rejects(curriculum, "courses/A01.json")


@pytest.mark.parametrize("conditional", [[{"course": "M03"}], [{"course": "M03", "when": ""}], [{"course": "M03", "when": "   "}]])
def test_reject_missing_conditional_explanation(curriculum, conditional):
    edit(curriculum, "dependencies.json", lambda d: d["M04"].update(conditional=conditional))
    rejects(curriculum, "dependencies.json")


@pytest.mark.parametrize("change", [
    lambda d: d.pop("A01"),
    lambda d: d["A01"].update(all_of=["UNKNOWN"]),
    lambda d: d["A01"].update(all_of=["A01"]),
    lambda d: d["A01"]["all_of"].append("F02"),
    lambda d: d["A01"].update(recommended=["F02"]),
    lambda d: d["S02"].update(any_of=[["S01-C"]]),
    lambda d: d["S02"].update(any_of=[["S01-C", "S01-C"]]),
    lambda d: d["S02"].update(any_of=[["S01-C", "S01-O"], ["F01", "F02"]]),
    lambda d: d["S02"].update(all_of=["S01-C"]),
    lambda d: d["F01"].update(all_of=["F02"]),
])
def test_reject_invalid_dependencies(curriculum, change):
    edit(curriculum, "dependencies.json", change)
    rejects(curriculum, "dependencies.json")


def test_reject_duplicate_edge(curriculum):
    def duplicate(d):
        edge = next(e for e in d["elements"] if "data-a" in e["attrs"])
        d["elements"].append(edge)
    edit(curriculum, "layout.json", duplicate)
    rejects(curriculum, "layout.json.*Duplicate relationship")


@pytest.mark.parametrize("change", [
    lambda d: d["elements"].append(next(e for e in d["elements"] if "course_id" in e)),
    lambda d: d["elements"].remove(next(e for e in d["elements"] if "course_id" in e)),
    lambda d: next(e for e in d["elements"] if "course_id" in e)["attrs"].update({"data-id": "A01"}),
    lambda d: next(e for e in d["elements"] if "course_id" in e).pop("course_id"),
    lambda d: d["elements"].remove(next(e for e in d["elements"] if "data-a" in e["attrs"])),
    lambda d: next(e for e in d["elements"] if "data-a" in e["attrs"])["attrs"].update({"data-a": "UNKNOWN"}),
    lambda d: next(e for e in d["elements"] if "data-a" in e["attrs"])["attrs"].update({"class": "flow-edge recommended"}),
    lambda d: d["elements"].remove(next(e for e in d["elements"] if "data-gate" in e["attrs"])),
    lambda d: d["elements"].append(next(e for e in d["elements"] if "data-gate" in e["attrs"])),
    lambda d: d["elements"].remove(next(e for e in d["elements"] if "data-goal" in e["attrs"])),
    lambda d: d["elements"].append(next(e for e in d["elements"] if "data-goal" in e["attrs"])),
])
def test_reject_inconsistent_layout(curriculum, change):
    edit(curriculum, "layout.json", change)
    rejects(curriculum, "layout.json")


def test_reject_missing_or_gate_parent(curriculum):
    edit(curriculum, "layout.json", lambda d: d["elements"].remove(next(
        e for e in d["elements"] if e["attrs"].get("data-a") == "S01-C"
        and e["attrs"].get("data-b") == "gate-cli"
    )))
    rejects(curriculum, "layout.json")


@pytest.mark.parametrize("tag,label", [("title", None), ("rect", None), ("text", "node-id"), ("text", "node-status"), ("text", "node-title")])
def test_reject_course_nodes_that_would_break_rendering(curriculum, tag, label):
    def remove_child(layout):
        course = next(e for e in layout["elements"] if "course_id" in e)
        course["children"] = [child for child in course["children"] if not (
            child["tag"] == tag and (label is None or label in child["attrs"].get("class", "").split())
        )]
    edit(curriculum, "layout.json", remove_child)
    rejects(curriculum, "layout.json")


def test_reject_duplicate_svg_ids(curriculum):
    edit(curriculum, "layout.json", lambda d: d["elements"].append({
        "tag": "g", "attrs": {"id": d["svg"]["id"]}
    }))
    rejects(curriculum, "layout.json.*SVG ids must be unique")


@pytest.mark.parametrize("change,message", [
    (lambda d: d["courses/A01.json"].update(mvp=0), "MVP"),
    (lambda d: d["learning-goals.json"].update({"LG-06": "New goal"}), "learning goals"),
    (lambda d: d["audiences.json"].update(other={"label": "Other", "help": "Other"}), "audiences"),
    (lambda d: d["dependencies.json"]["S02"].update(all_of=["S01-C", "S01-O"], any_of=[]), "CLI"),
    (lambda d: d["dependencies.json"]["S04"].update(all_of=[], any_of=[["S02", "S03"]]), "S04"),
    (lambda d: d["dependencies.json"]["M04"].update(all_of=["M02", "M03"], conditional=[]), "M04"),
    (lambda d: d["dependencies.json"]["A07"].update(all_of=["A02", "A05", "A06"], any_of=[]), "A07"),
    (lambda d: d["dependencies.json"]["A04"].update(all_of=["A03"], recommended=[]), "A04"),
])
def test_reject_baseline_semantic_changes(change, message):
    documents = validator.load_curriculum()
    change(documents)
    rejects_baseline(documents, message)


def rejects_baseline(documents, message):
    with pytest.raises(ValueError, match=message):
        validator.validate_baseline(documents)


def test_reject_changed_course_count():
    documents = validator.load_curriculum()
    documents["roadmap.json"]["course_ids"].pop()
    rejects_baseline(documents, "29")


def test_reject_changed_relationship_count():
    documents = validator.load_curriculum()
    documents["dependencies.json"]["U01"]["all_of"] = []
    rejects_baseline(documents, "35")


def test_cli_reports_invalid_data_without_traceback(curriculum):
    edit(curriculum, "courses/A01.json", lambda c: c.update(learn=[]))
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_ai_roadmap.py"), "--data-dir", str(curriculum)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "courses/A01.json/learn" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("url", [
    "https://user:password@example.org/", "https://example.org:invalid/", "https:///",
    "https://example.org/\x00unsafe", 'https://example.org/"onmouseover="unsafe',
    "https://example.org\\unsafe", "https://bad<host>/",
])
def test_reject_unsafe_https_urls(curriculum, url):
    edit(curriculum, "bibliography.json", lambda d: d["httpx"].update(url=url))
    rejects(curriculum, "bibliography.json")


@pytest.mark.parametrize("citation", [
    '<em onclick="unsafe">Title</em>', '<img src="unsafe">', '<script>unsafe</script>',
    '<em>Unclosed', '</em>Unopened', '<!-- hidden markup -->',
])
def test_reject_unsupported_citation_markup(curriculum, citation):
    edit(curriculum, "bibliography.json", lambda d: d["httpx"].update(citation=citation))
    rejects(curriculum, "bibliography.json")


@pytest.mark.parametrize("attrs", [
    {"fill": "url(https://example.org/unsafe)"},
    {"stroke": "url(javascript:unsafe)"},
    {"marker-end": "url(https://example.org/unsafe)"},
    {"onload": "unsafe"},
])
def test_reject_unsafe_svg_attributes(curriculum, attrs):
    edit(curriculum, "layout.json", lambda d: d["elements"][1]["attrs"].update(attrs))
    rejects(curriculum, "layout.json")
