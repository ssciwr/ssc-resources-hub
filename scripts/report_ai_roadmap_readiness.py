"""Report draft specification gaps; field completeness does not certify teaching readiness."""

import argparse
import json
from pathlib import Path

from validate_ai_roadmap import DATA, load_curriculum, validate_curriculum

FIELDS = ("instructors", "practice", "acceptance")
MANUAL_REVIEW = {
    "four_hour_feasibility": "Time a trial delivery, including setup and practical work, within four hours.",
    "project_scope": "Confirm at most two small projects and measurable acceptance checks.",
    "exercise_reproducibility": "Provide versioned exercise assets, environments and independently tested instructions.",
    "dataset_licensing": "Record dataset/model provenance, versions and rights for the intended reuse.",
    "cross_cutting_competencies": "Map responsible AI, security/privacy, evaluation/validation and reproducibility to activities.",
    "bibliography_review": "Check course-specific IEEE references, relevance and publication rights.",
}


def build_report(documents, mvp_only=False):
    courses = []
    for course_id in documents["roadmap.json"]["course_ids"]:
        course = documents[f"courses/{course_id}.json"]
        if mvp_only and not course["mvp"]:
            continue
        courses.append({
            "id": course_id,
            "name": course["name"],
            "mvp": bool(course["mvp"]),
            "missing_fields": [field for field in FIELDS if not course.get(field)],
        })
    return {
        "scope": "mvp" if mvp_only else "all",
        "teaching_readiness": "not_assessed",
        "missing_counts": {
            field: sum(field in course["missing_fields"] for course in courses)
            for field in FIELDS
        },
        "courses": courses,
        "manual_review_required": MANUAL_REVIEW,
    }


def print_report(report):
    courses = report["courses"]
    print(f"AI Roadmap draft specifications: {len(courses)} course options ({report['scope']})")
    print("Teaching readiness: not assessed\n")
    for field, count in report["missing_counts"].items():
        print(f"Missing {field}: {count}")
    print("\nCourse   Release  Missing fields")
    for course in courses:
        missing = ", ".join(course["missing_fields"]) or "None missing (field checks only)"
        release = "MVP" if course["mvp"] else "Future"
        print(f"{course['id']:<8} {release:<8} {missing}")
    print("\nManual review is required for every course, including those with complete fields:")
    for description in report["manual_review_required"].values():
        print(f"- {description}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA)
    parser.add_argument("--mvp", action="store_true", help="Report only MVP course options, retaining both CLI alternatives")
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON on stdout")
    args = parser.parse_args()
    try:
        validate_curriculum(args.data_dir)
        report = build_report(load_curriculum(args.data_dir), mvp_only=args.mvp)
    except ValueError as error:
        parser.exit(1, f"Cannot report on invalid curriculum: {error}\n")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
