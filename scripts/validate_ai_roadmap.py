"""Validate the public roadmap's schemas, references, relationships and baseline.

Run with ``uv run --no-sync python scripts/validate_ai_roadmap.py``.
This validates publication structure, not the sensitivity of prose or teaching readiness.
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from functools import lru_cache
from graphlib import CycleError, TopologicalSorter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/learn/ai-roadmap/data"
SCHEMAS = ROOT / "schemas"
REGISTRIES = ("roadmap", "learning-goals", "audiences", "dependencies",
              "bibliography", "instructors", "layout")
KINDS = {"required", "alternative", "recommended", "conditional"}


def require(condition, location, message):
    if not condition:
        raise ValueError(f"{location}: {message}")


def read_json(path):
    """Reject duplicate object keys instead of silently dropping public content."""
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, path, f"Duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"{path}: {error}") from error


def load_curriculum(data_dir=DATA):
    data_dir = Path(data_dir)
    documents = {f"{name}.json": read_json(data_dir / f"{name}.json") for name in REGISTRIES}
    documents.update({f"courses/{path.name}": read_json(path)
                      for path in sorted((data_dir / "courses").glob("*.json"))})
    return documents


@lru_cache(maxsize=None)
def schema_validator(name):
    filename = "course.schema.json" if name == "course" else "curriculum.schema.json"
    schema = read_json(SCHEMAS / filename)
    Draft202012Validator.check_schema(schema)
    if name != "course":
        schema = {**schema, "$ref": f"#/$defs/{name}"}
    return Draft202012Validator(schema)


def validate_schemas(documents):
    for filename, document in documents.items():
        name = "course" if filename.startswith("courses/") else filename.removesuffix(".json")
        validate_document(filename, name, document)


def validate_document(filename, name, document):
    error = next(schema_validator(name).iter_errors(document), None)
    if error:
        pointer = "/".join(str(part) for part in error.absolute_path)
        raise ValueError(f"{filename}/{pointer}: {error.message}")


def validate_https_url(value, location):
    require(not re.search(r'[\s\x00-\x1f\x7f<>"\\]', value), location,
            "HTTPS URLs cannot contain whitespace, controls, quotes or backslashes")
    try:
        url = urlsplit(value)
        _ = url.port  # Accessing the property validates syntax and range.
        valid = url.scheme == "https" and url.hostname and url.username is None and url.password is None
    except ValueError as error:
        raise ValueError(f"{location}: Invalid HTTPS URL") from error
    require(valid, location, "A complete HTTPS URL without embedded credentials is required")


class CitationMarkup(HTMLParser):
    """Allow only balanced, attribute-free emphasis in bibliography citations."""

    def __init__(self, location):
        super().__init__(convert_charrefs=False)
        self.location = location
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        require(tag == "em" and not attrs and self.get_starttag_text().lower() == "<em>",
                self.location, "Citations support only attribute-free <em> markup")
        self.depth += 1

    def handle_endtag(self, tag):
        require(tag == "em" and self.depth > 0, self.location, "Unbalanced citation markup")
        self.depth -= 1

    def handle_startendtag(self, tag, attrs):
        raise ValueError(f"{self.location}: Self-closing citation markup is unsupported")

    def handle_comment(self, data):
        raise ValueError(f"{self.location}: Citation comments are unsupported")

    def handle_decl(self, decl):
        raise ValueError(f"{self.location}: Citation declarations are unsupported")

    def handle_pi(self, data):
        raise ValueError(f"{self.location}: Citation processing instructions are unsupported")

    def unknown_decl(self, data):
        raise ValueError(f"{self.location}: Unsupported citation declaration")


def validate_content(documents):
    for key, reference in documents["bibliography.json"].items():
        location = f"bibliography.json/{key}"
        if reference["url"]:
            validate_https_url(reference["url"], location + "/url")
        parser = CitationMarkup(location + "/citation")
        parser.feed(reference["citation"])
        parser.close()
        require(parser.depth == 0, location, "Unclosed citation emphasis")
    for key, instructor in documents["instructors.json"].items():
        for field in ("github", "source", "avatar"):
            if field in instructor:
                validate_https_url(instructor[field], f"instructors.json/{key}/{field}")


def validate_references(documents):
    ids = documents["roadmap.json"]["course_ids"]
    expected = {f"courses/{course_id}.json" for course_id in ids}
    actual = {name for name in documents if name.startswith("courses/")}
    require(expected == actual, "roadmap.json/course_ids",
            f"Course files differ: missing {sorted(expected - actual)}, unlisted {sorted(actual - expected)}")
    for course_id in ids:
        filename = f"courses/{course_id}.json"
        course = documents[filename]
        require(course["id"] == course_id, filename, "Course id must match filename and manifest")
        for field, registry in (("goal", "learning-goals"), ("roles", "audiences"),
                                ("instructors", "instructors"), ("references", "bibliography")):
            values = [course[field]] if field == "goal" else course[field]
            unknown = set(values) - documents[f"{registry}.json"].keys()
            require(not unknown, f"{filename}/{field}", f"Unknown references: {sorted(unknown)}")
        require(len(course["modules"]) == len(course["moduleDescriptions"]), filename,
                "modules and moduleDescriptions must have equal lengths")


def relationships(dependencies):
    for target, spec in dependencies.items():
        for source in spec["all_of"]:
            yield source, target, "required"
        for group in spec["any_of"]:
            for source in group:
                yield source, target, "alternative"
        for source in spec["recommended"]:
            yield source, target, "recommended"
        for item in spec["conditional"]:
            yield item["course"], target, "conditional"


def validate_dependencies(dependencies, ids):
    location = "dependencies.json"
    require(set(dependencies) == set(ids), location, "Dependency targets must match course ids")
    graph = TopologicalSorter({course_id: set() for course_id in ids})
    seen = set()
    for source, target, kind in relationships(dependencies):
        require(source in ids, location, f"Unknown prerequisite {source!r} for {target}")
        require(source != target, location, f"Self dependency at {target}")
        pair = source, target
        require(pair not in seen, location,
                f"Repeated prerequisite {source} for {target}, including across relationship kinds")
        seen.add(pair)
        graph.add(target, source)
    try:
        # Preserve the migration's cycle policy across all relationship kinds.
        list(graph.static_order())
    except CycleError as error:
        raise ValueError(f"{location}: Circular dependency: {' -> '.join(error.args[1])}") from error


def walk_elements(elements):
    for element in elements:
        yield element
        yield from walk_elements(element.get("children", []))


def validate_layout(layout, dependencies, ids):
    location = "layout.json"
    nodes = list(walk_elements(layout["elements"]))
    svg_ids = [layout["svg"]["id"]] + [n["attrs"]["id"] for n in nodes if "id" in n["attrs"]]
    require(len(svg_ids) == len(set(svg_ids)), location, "SVG ids must be unique")
    lanes = [n["attrs"]["data-goal"] for n in nodes if "data-goal" in n["attrs"]]
    require(Counter(lanes) == Counter(f"LG-{number:02}" for number in range(1, 6)),
            location, "Each of the five learning goal lanes must render exactly once")
    courses = []
    gates = []
    segments = Counter()
    incoming, outgoing = defaultdict(set), defaultdict(set)
    actual = Counter()
    for node in nodes:
        attrs = node["attrs"]
        classes = set(attrs.get("class", "").split())
        if "course_id" in node or "course-link" in classes:
            course_id = node.get("course_id")
            require(course_id in ids and attrs.get("data-id") == course_id, location,
                    "Rendered course must have matching course_id and data-id")
            require(node["tag"] == "g" and "course-link" in classes, location,
                    f"Course {course_id} must be an interactive SVG group")
            require(any(c["tag"] == "title" for c in node.get("children", [])), location,
                    f"Course {course_id} needs an accessible title")
            children = list(walk_elements(node.get("children", [])))
            require(sum(c["tag"] == "rect" for c in children) == 1, location,
                    f"Course {course_id} needs one rectangle")
            for label in ("node-id", "node-status", "node-title"):
                require(any(label in c["attrs"].get("class", "").split() for c in children),
                        location, f"Course {course_id} needs a {label} label")
            courses.append(course_id)
        elif "data-id" in attrs:
            raise ValueError(f"{location}: data-id outside a course node")
        if "choice-gate" in classes or "data-gate" in attrs:
            require("choice-gate" in classes and "data-gate" in attrs, location,
                    "OR gate must have a class and data-gate identifier")
            gates.append("gate-" + attrs["data-gate"])
        if "flow-edge" not in classes and not ({"data-a", "data-b"} & attrs.keys()):
            continue
        source, target = attrs.get("data-a"), attrs.get("data-b")
        kinds = classes & KINDS
        require("flow-edge" in classes and len(kinds) == 1 and source and target, location,
                "Relationship needs data-a, data-b, flow-edge and exactly one kind")
        kind = next(iter(kinds))
        segment = source, target, kind
        segments[segment] += 1
        require(segments[segment] == 1, location, f"Duplicate relationship segment {segment}")
        source_gate, target_gate = source.startswith("gate-"), target.startswith("gate-")
        require(not (source_gate and target_gate), location, "OR gates cannot connect to each other")
        require((source_gate or source in ids) and (target_gate or target in ids), location,
                f"Unknown relationship endpoint {source} -> {target}")
        if source_gate or target_gate:
            require(kind == "alternative", location, "OR gate segments must be alternative relationships")
            if target_gate:
                incoming[target].add(source)
            else:
                outgoing[source].add(target)
        else:
            actual[segment] += 1
    require(Counter(courses) == Counter(ids), location, "Each course must render exactly once")
    require(set(incoming) == set(outgoing), location, "OR gates need incoming and outgoing edges")
    require(Counter(gates) == Counter(incoming.keys()), location,
            "Each connected OR gate must render exactly once")
    for gate, parents in incoming.items():
        for target in outgoing[gate]:
            require(len(dependencies[target]["any_of"]) == 1
                    and set(dependencies[target]["any_of"][0]) == parents,
                    location, f"OR gate {gate} does not match alternatives for {target}")
            actual.update((source, target, "alternative") for source in parents)
    require(actual == Counter(relationships(dependencies)), location,
            "Diagram relationships do not match dependencies.json")


def validate_baseline(documents):
    """Freeze migration counts and the established AND/OR/conditional meaning."""
    ids = documents["roadmap.json"]["course_ids"]
    deps = documents["dependencies.json"]
    require(len(ids) == 29, "roadmap.json", "Migration baseline requires 29 courses")
    counts = Counter(documents[f"courses/{course_id}.json"]["mvp"] for course_id in ids)
    require(counts == {1: 13, 0: 16}, "roadmap.json", "Migration baseline requires 13 MVP and 16 future courses")
    require(set(documents["learning-goals.json"]) == {"F", "LG-01", "LG-02", "LG-03", "LG-04", "LG-05"},
            "learning-goals.json", "Migration baseline requires five learning goals and shared foundations")
    require(set(documents["audiences.json"]) == {"students", "researchers", "academic", "technical"},
            "audiences.json", "Migration baseline requires the four established audiences")
    cli = {"S01-C", "S01-O"}
    require(deps["S01-C"] == deps["S01-O"], "dependencies.json", "CLI alternatives must have equivalent prerequisites")
    for target in ("S02", "S03"):
        spec = deps[target]
        require(not spec["all_of"] and len(spec["any_of"]) == 1 and set(spec["any_of"][0]) == cli,
                "dependencies.json", f"{target} must accept either CLI, without requiring both")
    for target, spec in deps.items():
        require(not cli.intersection(spec["all_of"]), "dependencies.json",
                f"{target} must not mandate an individual CLI alternative")
        for group in spec["any_of"]:
            require(not cli.intersection(group) or cli <= set(group), "dependencies.json",
                    f"{target} must offer both equivalent CLI alternatives")
    require(set(deps["S04"]["all_of"]) == {"S02", "S03"} and not deps["S04"]["any_of"],
            "dependencies.json", "S04 requires both S02 AND S03")
    require(deps["A07"]["all_of"] == [] and len(deps["A07"]["any_of"]) == 1
            and set(deps["A07"]["any_of"][0]) == {"A02", "A05", "A06"},
            "dependencies.json", "A07 requires any one of A02, A05 or A06")
    require(deps["A04"]["all_of"] == [] and deps["A04"]["recommended"] == ["A03"],
            "dependencies.json", "A03 is recommended, not mandatory, for A04")
    require(deps["M04"]["all_of"] == ["M02"] and deps["M04"]["conditional"] == [
        {"course": "M03", "when": "LLM-serving variant only"}
    ], "dependencies.json", "M04 requires M02; M03 is conditional on the LLM-serving variant")
    require(len(list(relationships(deps))) == 35, "dependencies.json", "Migration baseline requires 35 relationships")


def validate_curriculum(data_dir=DATA):
    data_dir = Path(data_dir)
    documents = load_curriculum(data_dir)
    validate_document("roadmap.json", "roadmap", documents["roadmap.json"])
    expected = {f"{name}.json" for name in REGISTRIES} | {
        f"courses/{course_id}.json" for course_id in documents["roadmap.json"]["course_ids"]
    }
    files = {path.relative_to(data_dir).as_posix() for path in data_dir.rglob("*") if path.is_file()}
    require(not files - expected, data_dir, f"Unexpected public data files: {sorted(files - expected)}")
    validate_schemas(documents)
    validate_content(documents)
    validate_references(documents)
    ids = documents["roadmap.json"]["course_ids"]
    dependencies = documents["dependencies.json"]
    validate_dependencies(dependencies, ids)
    validate_layout(documents["layout.json"], dependencies, ids)
    validate_baseline(documents)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA)
    args = parser.parse_args()
    try:
        validate_curriculum(args.data_dir)
    except ValueError as error:
        parser.exit(1, f"Invalid AI roadmap: {error}\n")
    print("Public AI roadmap validated: 29 courses, 13 MVP, 16 future, 35 relationships.")


if __name__ == "__main__":
    main()
