"""Browser regressions against the generated site, its ES modules and HTTP JSON."""

import base64
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.browser
DATA = Path(__file__).resolve().parents[2] / "docs/learn/ai-roadmap/data"
MANIFEST = json.loads((DATA / "roadmap.json").read_text(encoding="utf-8"))
COURSES = {
    course_id: json.loads((DATA / f"courses/{course_id}.json").read_text(encoding="utf-8"))
    for course_id in MANIFEST["course_ids"]
}
AUDIENCES = json.loads((DATA / "audiences.json").read_text(encoding="utf-8"))
INSTRUCTOR = json.loads((DATA / "instructors.json").read_text(encoding="utf-8"))["lkeegan"]
GOAL_COURSES = {
    "F": {"F01", "F02"},
    "LG-01": {"F01", "U01"},
    "LG-02": {"F01", "F02", "R01", "R02"},
    "LG-03": {"F01", "F02", "S01-C", "S01-O", "S02", "S03", "S04", "S05",
              "S06", "S07", "S08", "S09", "S10"},
    "LG-04": {"F01", "F02", "A01", "A02", "A03", "A04", "A05", "A06", "A07", "A08", "A09"},
    "LG-05": {"F01", "F02", "A01", "M01", "M02", "M03", "M04"},
}


@pytest.fixture
def roadmap(page, roadmap_url):
    origin = urlsplit(roadmap_url).netloc
    errors = []

    def local(url):
        return urlsplit(url).netloc == origin

    def route_request(route):
        # Tests must work without external fonts, avatars or third-party services.
        if local(route.request.url):
            route.continue_()
        else:
            route.abort()

    page.route("**/*", route_request)
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("response", lambda response: errors.append(
        f"HTTP {response.status}: {response.url}"
    ) if local(response.url) and response.status >= 400 else None)
    page.on("requestfailed", lambda request: errors.append(
        f"{request.failure}: {request.url}"
    ) if local(request.url) else None)
    page.on("console", lambda message: errors.append(message.text)
            if message.type == "error" and local(message.location.get("url", "")) else None)
    page.goto(roadmap_url, wait_until="domcontentloaded")
    expect(page.locator(".course-link")).to_have_count(29)
    expect(page.locator("#catalogue tr")).to_have_count(29)
    expect(page.locator("#roadmapError")).to_be_hidden()
    yield page
    assert not errors, "Browser runtime or local asset errors:\n" + "\n".join(errors)


def highlighted(page):
    return set(page.locator(".course-link:not(.dim)").evaluate_all(
        "nodes => nodes.map(node => node.dataset.id)"
    ))


def choose_audience(page, audience):
    page.locator("#roleToggle").click()
    page.locator(f'input[name="audienceChoice"][value="{audience}"]').check()
    expect(page.locator("#audienceOptions")).to_be_hidden()


def open_course(page, course_id):
    page.locator(f'.course-link[data-id="{course_id}"]').click()
    expect(page.locator("#detail")).to_be_visible()
    expect(page.locator("#detailTitle")).to_have_text(COURSES[course_id]["name"])


@pytest.mark.parametrize("course_id", MANIFEST["course_ids"])
def test_every_course_dialog(roadmap, course_id):
    open_course(roadmap, course_id)
    expect(roadmap.locator("#detailMeta")).to_contain_text(course_id)
    expect(roadmap.locator("#detailBody h3").first).to_have_text("Prerequisites")
    for heading in ["Description", "Instructors", "What you will learn", "Tools you will learn",
                    "Modules", "Intended learners", "Enables", "Learner bibliography"]:
        expect(roadmap.locator("#detail").get_by_role("heading", name=heading, exact=True)).to_be_visible()
    expect(roadmap.locator("#detail .module-list > li")).to_have_count(len(COURSES[course_id]["modules"]))
    expect(roadmap.locator("#detail .bib-list > li")).to_have_count(len(COURSES[course_id]["references"]))
    roadmap.get_by_role("button", name="Close course details").click()
    expect(roadmap.locator("#detail")).to_be_hidden()
    expect(roadmap.locator(".course-link.selected")).to_have_count(0)


@pytest.mark.parametrize("source,target", [
    ("S02", "S01-C"), ("S03", "S01-O"), ("A07", "A05"), ("A04", "A03"), ("M04", "M03"),
])
def test_prerequisite_navigation(roadmap, source, target):
    open_course(roadmap, source)
    roadmap.locator(f'.prereq-card [data-open="{target}"]').click()
    expect(roadmap.locator("#detailTitle")).to_have_text(COURSES[target]["name"])
    expect(roadmap.locator(f'.course-link[data-id="{target}"]')).to_have_class(re.compile(r"selected"))


@pytest.mark.parametrize("goal,expected", GOAL_COURSES.items())
def test_learning_goal_selection(roadmap, goal, expected):
    roadmap.get_by_label("Learning goal", exact=True).select_option(goal)
    assert highlighted(roadmap) == expected
    expect(roadmap.locator("#catalogue tr")).to_have_count(len(expected))
    expect(roadmap.locator(".course-link")).to_have_count(29)
    expect(roadmap.locator(".course-link:visible")).to_have_count(29)


@pytest.mark.parametrize("audience", AUDIENCES)
def test_audience_selection(roadmap, audience):
    roadmap.locator("#roleToggle").click()
    option = roadmap.locator(".audience-option").filter(has=roadmap.locator(
        f'input[value="{audience}"]'
    ))
    expect(option.locator("small")).to_have_text(AUDIENCES[audience]["help"])
    option.get_by_role("radio").check()
    expect(roadmap.locator("#roleLabel")).to_have_text(AUDIENCES[audience]["label"])
    assert highlighted(roadmap) == {key for key, c in COURSES.items() if audience in c["roles"]}
    expect(roadmap.locator(".course-link:visible")).to_have_count(29)


def test_search_precedence_and_filter_restoration(roadmap):
    roadmap.locator("#goal").select_option("LG-01")
    choose_audience(roadmap, "academic")
    before = highlighted(roadmap)
    assert "A01" not in before
    roadmap.get_by_label("Find a course").fill("  a01  ")
    assert highlighted(roadmap) == {"A01"}
    expect(roadmap.locator("#matchCount")).to_contain_text("all goals and audiences")
    expect(roadmap.locator("#goal")).to_have_value("LG-01")
    expect(roadmap.locator("#role")).to_have_value("academic")
    roadmap.get_by_label("Find a course").clear()
    assert highlighted(roadmap) == before


def test_changing_filters_during_search_restores_latest_values(roadmap):
    roadmap.locator("#search").fill("A01")
    roadmap.locator("#goal").select_option("LG-05")
    choose_audience(roadmap, "technical")
    assert highlighted(roadmap) == {"A01"}
    roadmap.locator("#search").clear()
    assert highlighted(roadmap) == GOAL_COURSES["LG-05"]


@pytest.mark.parametrize("query", ["PROGRAMMATIC", "HTTPX", "timeouts"])
def test_search_course_content(roadmap, query):
    roadmap.locator("#search").fill(query)
    assert "A01" in highlighted(roadmap)


def test_no_results_keeps_complete_diagram(roadmap):
    roadmap.locator("#search").fill("no-course-matches-this-query")
    expect(roadmap.locator("#empty")).to_be_visible()
    expect(roadmap.locator("#catalogue tr")).to_have_count(0)
    expect(roadmap.locator(".course-link.dim:visible")).to_have_count(29)


def test_reset(roadmap):
    roadmap.locator("#goal").select_option("LG-02")
    choose_audience(roadmap, "academic")
    roadmap.locator("#search").fill("A01")
    roadmap.locator("#roleToggle").click()
    roadmap.get_by_role("button", name="Reset", exact=True).click()
    for control in ["goal", "role", "search"]:
        expect(roadmap.locator(f"#{control}")).to_have_value("")
    expect(roadmap.locator("#roleLabel")).to_have_text("All learners")
    expect(roadmap.locator("#audienceOptions")).to_be_hidden()
    assert highlighted(roadmap) == set(COURSES)
    expect(roadmap.locator("#catalogue tr")).to_have_count(29)


def test_zoom_and_fit(roadmap):
    roadmap.get_by_role("button", name="100%", exact=True).click()
    expect(roadmap.locator("#zoomLevel")).to_have_text("100%")
    roadmap.get_by_role("button", name="Zoom in", exact=True).click()
    expect(roadmap.locator("#zoomLevel")).to_have_text("120%")
    roadmap.get_by_role("button", name="Zoom out", exact=True).click()
    expect(roadmap.locator("#zoomLevel")).to_have_text("100%")
    roadmap.locator("#canvas").evaluate("element => element.scrollLeft = 100")
    roadmap.get_by_role("button", name="Fit map", exact=True).click()
    assert 15 <= int(roadmap.locator("#zoomLevel").inner_text().rstrip("%")) < 100
    assert roadmap.locator("#canvas").evaluate("element => element.scrollLeft") == 0
    box = roadmap.locator("#canvas").bounding_box()
    assert roadmap.locator("#overview").bounding_box()["width"] <= box["width"]


def test_instructor_profile_and_offline_initials(roadmap):
    open_course(roadmap, "S03")
    card = roadmap.locator(".instructor-card")
    expect(card).to_have_count(1)
    expect(card.locator("strong")).to_have_text(INSTRUCTOR["name"])
    expect(card.locator(".instructor-position")).to_have_text(INSTRUCTOR["position"])
    expect(card.locator("small")).to_have_text(INSTRUCTOR["affiliation"])
    expect(card.get_by_role("link", name=re.compile("GitHub"))).to_have_attribute("href", INSTRUCTOR["github"])
    expect(card.locator("img")).to_be_hidden()
    expect(card.locator(".instructor-avatar > span")).to_have_text(INSTRUCTOR["initials"])
    expect(card.locator(".instructor-avatar > span")).to_be_visible()


def test_instructor_avatar_when_available(roadmap):
    # A deterministic image avoids depending on GitHub uptime or external access.
    pixel = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")
    roadmap.route(INSTRUCTOR["avatar"], lambda route: route.fulfill(content_type="image/png", body=pixel))
    open_course(roadmap, "S03")
    image = roadmap.locator(".instructor-avatar img")
    expect(image).to_be_visible()
    expect(image).to_have_js_property("complete", True)
    assert image.evaluate("image => image.naturalWidth") == 1


def test_multiple_instructor_profiles(roadmap):
    # Reuse documented information without inventing an instructor identity.
    second = {key: value for key, value in INSTRUCTOR.items() if key != "avatar"}
    profiles = {"lkeegan": INSTRUCTOR, "test-profile-without-avatar": second}
    course = {**COURSES["S03"], "instructors": list(profiles)}
    roadmap.route("**/data/instructors.json", lambda route: route.fulfill(json=profiles))
    roadmap.route("**/data/courses/S03.json", lambda route: route.fulfill(json=course))
    roadmap.reload(wait_until="domcontentloaded")
    expect(roadmap.locator("#catalogue tr")).to_have_count(29)
    open_course(roadmap, "S03")
    expect(roadmap.locator(".instructor-card")).to_have_count(2)
    expect(roadmap.locator(".instructor-card").nth(1).locator("img")).to_have_count(0)
    expect(roadmap.locator(".instructor-card").nth(1).locator(".instructor-avatar > span")).to_have_text(INSTRUCTOR["initials"])


def test_unassigned_instructor_placeholder(roadmap):
    open_course(roadmap, "F01")
    expect(roadmap.locator(".instructor-pending")).to_have_text("To be confirmed.")


@pytest.mark.parametrize("width", [320, 390, 768, 1440])
def test_responsive_layout(roadmap, width):
    roadmap.set_viewport_size({"width": width, "height": 900})
    roadmap.get_by_role("button", name="Fit map", exact=True).click()
    assert roadmap.evaluate("document.documentElement.scrollWidth <= innerWidth")
    expect(roadmap.locator(".course-link:visible")).to_have_count(29)
    open_course(roadmap, "S03")
    dialog = roadmap.locator("#detail").bounding_box()
    assert dialog["x"] >= 0 and dialog["x"] + dialog["width"] <= width + 1
    assert roadmap.locator("#detail").evaluate("element => element.scrollWidth <= element.clientWidth")
    roadmap.get_by_role("button", name="Close course details").click()
    choose_audience(roadmap, "researchers")
    expect(roadmap.locator("#roleLabel")).to_have_text("Researchers")


def test_keyboard_prerequisite_navigation_keeps_focus(roadmap):
    node = roadmap.locator('.course-link[data-id="S02"]')
    node.focus()
    node.press("Enter")
    expect(roadmap.locator("#detail")).to_be_visible()
    prerequisite = roadmap.locator('.prereq-card [data-open="S01-O"]')
    prerequisite.focus()
    prerequisite.press("Enter")
    expect(roadmap.locator("#detailTitle")).to_have_text(COURSES["S01-O"]["name"])
    expect(roadmap.locator("#detailTitle")).to_be_focused()
    roadmap.keyboard.press("Escape")
    expect(roadmap.locator("#detail")).to_be_hidden()
    expect(node).to_be_focused()


def test_keyboard_audience_picker(roadmap):
    roadmap.locator("#roleToggle").focus()
    roadmap.keyboard.press("Enter")
    selected = roadmap.locator('input[name="audienceChoice"][value=""]')
    expect(selected).to_be_focused()
    roadmap.keyboard.press("ArrowDown")
    expect(roadmap.locator('input[name="audienceChoice"][value="students"]')).to_be_checked()
    expect(roadmap.locator("#audienceOptions")).to_be_visible()
    roadmap.keyboard.press("Enter")
    expect(roadmap.locator("#audienceOptions")).to_be_hidden()
    expect(roadmap.locator("#roleToggle")).to_be_focused()
    expect(roadmap.locator("#roleLabel")).to_have_text("Students")


def test_course_hash_opens_dialog(roadmap, roadmap_url):
    roadmap.goto("about:blank")
    roadmap.goto(roadmap_url + "#A01", wait_until="domcontentloaded")
    expect(roadmap.locator("#detailTitle")).to_have_text(COURSES["A01"]["name"])
    expect(roadmap.locator("#detail")).to_be_visible()


def test_failed_data_load_has_visible_error(page, roadmap_url):
    origin = urlsplit(roadmap_url).netloc
    page.route("**/*", lambda route: route.continue_()
               if urlsplit(route.request.url).netloc == origin else route.abort())
    page.route("**/data/courses/A01.json", lambda route: route.fulfill(status=404, body="Not found"))
    page.goto(roadmap_url, wait_until="domcontentloaded")
    expect(page.locator("#roadmapError")).to_be_visible()
    expect(page.locator("#roadmapError")).to_contain_text("The roadmap could not load")


def reload_dependencies(page, change):
    """Exercise presentation of hypothetical dependencies without editing curriculum files."""
    dependencies = json.loads((DATA / "dependencies.json").read_text(encoding="utf-8"))
    change(dependencies)
    page.route("**/data/dependencies.json", lambda route: route.fulfill(json=dependencies))
    page.reload(wait_until="domcontentloaded")
    expect(page.locator("#catalogue tr")).to_have_count(29)


def enables_section(page):
    return page.locator(".detail-bottom .detail-section").filter(
        has=page.get_by_role("heading", name="Enables", exact=True)
    )


def catalogue_prerequisites(page, course_id):
    return page.locator("#catalogue tr").filter(
        has=page.locator(f'[data-open="{course_id}"]')
    ).locator("td").last


@pytest.mark.parametrize("condition", ["Alternate serving exercise", 'Variant <local> & "safe"'])
def test_conditional_wording_comes_from_data(roadmap, condition):
    reload_dependencies(roadmap, lambda d: d["M04"]["conditional"][0].update(when=condition))
    cell = catalogue_prerequisites(roadmap, "M04")
    expect(cell).to_contain_text(f"M03 ({condition})")
    expect(roadmap.locator(".legend")).to_contain_text("Conditional (see course details)")
    open_course(roadmap, "M04")
    group = roadmap.locator(".prereq-card .conditional-relation")
    expect(group.locator(".conditional-note")).to_have_text(f"Conditional: {condition}")
    group.locator('[data-open="M03"]').click()
    group = enables_section(roadmap).locator(".conditional-relation")
    expect(group.locator(".conditional-note")).to_have_text(f"Conditional: {condition}")
    group.locator('[data-open="M04"]').click()
    expect(roadmap.locator("#detailTitle")).to_have_text(COURSES["M04"]["name"])


def test_removed_conditional_relationship_disappears(roadmap):
    reload_dependencies(roadmap, lambda d: d["M04"].update(conditional=[]))
    expect(catalogue_prerequisites(roadmap, "M04")).not_to_contain_text("M03")
    open_course(roadmap, "M04")
    expect(roadmap.locator(".prereq-card .conditional-note")).to_have_count(0)
    roadmap.locator("#close").click()
    open_course(roadmap, "M03")
    expect(enables_section(roadmap).locator(".conditional-note")).to_have_count(0)
    expect(enables_section(roadmap).locator('[data-open="M04"]')).to_have_count(0)


def test_multiple_conditional_relationships_are_not_course_specific(roadmap):
    additional = [
        {"course": "M03", "when": "Alternate runtime exercise"},
        {"course": "A03", "when": "Tool-serving exercise"},
    ]
    reload_dependencies(roadmap, lambda d: d["A08"].update(conditional=additional))
    cell = catalogue_prerequisites(roadmap, "A08")
    expect(cell).to_contain_text("A07")
    for item in additional:
        expect(cell).to_contain_text(f'{item["course"]} ({item["when"]})')
    open_course(roadmap, "A08")
    expect(roadmap.locator(".prereq-card .conditional-relation")).to_have_count(2)
    roadmap.locator('.prereq-card [data-open="M03"]').click()
    enabled = enables_section(roadmap)
    expect(enabled.locator(".conditional-relation")).to_have_count(2)
    expect(enabled.locator(".empty-list")).to_have_count(0)
    expect(enabled.locator('[data-open="A08"]')).to_have_count(1)
    expect(enabled.locator('[data-open="M04"]')).to_have_count(1)


def test_conditional_only_prerequisite_does_not_say_none(roadmap):
    reload_dependencies(roadmap, lambda d: d["U01"].update(
        all_of=[], conditional=[{"course": "M03", "when": "Optional model exercise"}]
    ))
    cell = catalogue_prerequisites(roadmap, "U01")
    expect(cell).to_contain_text("Conditional: M03 (Optional model exercise)")
    expect(cell).not_to_contain_text("None shown")
    open_course(roadmap, "U01")
    expect(roadmap.locator(".prereq-card .empty-list")).to_have_count(0)
    expect(roadmap.locator('.prereq-card .conditional-relation [data-open="M03"]')).to_have_count(1)


INJECTION_TEXT = '<img data-injected src="data:," onerror="window.__roadmapXss = true">'


def reload_records(page, records):
    for filename, record in records.items():
        page.route(f"**/data/{filename}", lambda route, request, value=record: route.fulfill(json=value))
    page.reload(wait_until="domcontentloaded")
    expect(page.locator("#catalogue tr")).to_have_count(29)


def assert_no_injected_markup(page):
    expect(page.locator("[data-injected]")).to_have_count(0)
    assert page.evaluate("window.__roadmapXss === undefined")


def test_course_content_is_rendered_as_text(roadmap):
    course = {**COURSES["A01"]}
    for field in ["name", "description", "coverage", "courseType", "prerequisiteRationale", "practice", "acceptance"]:
        course[field] = INJECTION_TEXT
    for field in ["prior", "learn", "tools", "modules", "moduleDescriptions"]:
        course[field] = [INJECTION_TEXT]
    reload_records(roadmap, {"courses/A01.json": course})
    expect(roadmap.locator('#catalogue [data-open="A01"]')).to_have_text(INJECTION_TEXT)
    roadmap.locator('.course-link[data-id="A01"] rect').click()
    expect(roadmap.locator("#detailTitle")).to_have_text(INJECTION_TEXT)
    expect(roadmap.locator(".description-copy")).to_have_text(INJECTION_TEXT)
    expect(roadmap.locator(".module-copy strong")).to_have_text(INJECTION_TEXT)
    expect(roadmap.locator(".module-copy small")).to_have_text(INJECTION_TEXT)
    expect(roadmap.locator("#detail .tools li")).to_have_text(INJECTION_TEXT)
    expect(roadmap.locator(".prereq-note").first).to_contain_text(INJECTION_TEXT)
    assert_no_injected_markup(roadmap)


def test_audience_goal_and_instructor_fields_are_text(roadmap):
    audiences = json.loads((DATA / "audiences.json").read_text())
    audiences["technical"] = {"label": INJECTION_TEXT, "help": INJECTION_TEXT}
    goals = json.loads((DATA / "learning-goals.json").read_text())
    goals["LG-04"] = INJECTION_TEXT
    instructor = {**INSTRUCTOR}
    for field in ["name", "initials", "position", "affiliation", "githubHandle"]:
        instructor[field] = INJECTION_TEXT
    reload_records(roadmap, {"audiences.json": audiences, "learning-goals.json": goals,
                            "instructors.json": {"lkeegan": instructor}})
    roadmap.locator("#roleToggle").click()
    option = roadmap.locator(".audience-option").filter(has=roadmap.locator('input[value="technical"]'))
    expect(option.locator("strong")).to_have_text(INJECTION_TEXT)
    expect(option.locator("small")).to_have_text(INJECTION_TEXT)
    option.get_by_role("radio").check()
    expect(roadmap.locator("#roleLabel")).to_have_text(INJECTION_TEXT)
    open_course(roadmap, "A01")
    expect(roadmap.locator("#detailMeta")).to_contain_text(INJECTION_TEXT)
    roadmap.locator("#close").click()
    open_course(roadmap, "S03")
    expect(roadmap.locator(".instructor-info strong")).to_have_text(INJECTION_TEXT)
    expect(roadmap.locator(".instructor-position")).to_have_text(INJECTION_TEXT)
    expect(roadmap.locator(".instructor-info small")).to_have_text(INJECTION_TEXT)
    expect(roadmap.locator(".instructor-avatar > span")).to_have_text(INJECTION_TEXT)
    assert_no_injected_markup(roadmap)


def test_bibliography_preserves_only_emphasis_markup(roadmap):
    bibliography = json.loads((DATA / "bibliography.json").read_text())
    bibliography["httpx"]["citation"] = f'Citation <em>Allowed & correct</em> {INJECTION_TEXT}'
    reload_records(roadmap, {"bibliography.json": bibliography})
    open_course(roadmap, "A01")
    reference = roadmap.locator(".bib-list > li").first
    expect(reference.locator("em")).to_have_text("Allowed & correct")
    expect(reference).to_contain_text(INJECTION_TEXT)
    assert_no_injected_markup(roadmap)


@pytest.mark.parametrize("url", [
    "javascript:window.__roadmapXss=true", "data:text/html,unsafe", "//example.org/unsafe",
    "https://user:password@example.org/", "https://example.org:invalid/", "https:///",
    "https://example.org/\nunsafe", 'https://example.org/"onmouseover="unsafe',
])
def test_unsafe_external_urls_are_not_rendered(roadmap, url):
    bibliography = json.loads((DATA / "bibliography.json").read_text())
    bibliography["httpx"]["url"] = url
    instructor = {**INSTRUCTOR, "github": url, "source": url, "avatar": url}
    reload_records(roadmap, {"bibliography.json": bibliography,
                            "instructors.json": {"lkeegan": instructor}})
    open_course(roadmap, "A01")
    expect(roadmap.locator(".bib-list > li").first.locator("a")).to_have_count(0)
    roadmap.locator("#close").click()
    open_course(roadmap, "S03")
    expect(roadmap.locator(".instructor-links a")).to_have_count(0)
    expect(roadmap.locator(".instructor-avatar img")).to_have_count(0)
    expect(roadmap.locator(".instructor-avatar > span")).to_be_visible()
    assert_no_injected_markup(roadmap)


def test_https_reference_query_is_preserved(roadmap):
    url = "https://example.org/read?author=O%27Brien&title=%22quoted%22"
    bibliography = json.loads((DATA / "bibliography.json").read_text())
    bibliography["httpx"]["url"] = url
    reload_records(roadmap, {"bibliography.json": bibliography})
    open_course(roadmap, "A01")
    expect(roadmap.locator(".bib-list > li").first.locator("a")).to_have_attribute("href", url)


@pytest.mark.parametrize("change", [
    lambda d: d["svg"].update(onload="window.__roadmapXss=true"),
    lambda d: d["elements"].append({"tag": "script", "attrs": {}, "text": "window.__roadmapXss=true"}),
    lambda d: d["elements"][1]["attrs"].update(style="background:url(https://example.org/unsafe)"),
    lambda d: d["elements"][1]["attrs"].update(fill="url(https://example.org/unsafe)"),
    lambda d: d["elements"][1]["attrs"].update({"marker-end": "url(javascript:unsafe)"}),
])
def test_unsafe_svg_layout_fails_closed(page, roadmap_url, change):
    layout = json.loads((DATA / "layout.json").read_text())
    change(layout)
    origin = urlsplit(roadmap_url).netloc
    page.route("**/*", lambda route: route.continue_()
               if urlsplit(route.request.url).netloc == origin else route.abort())
    page.route("**/data/layout.json", lambda route: route.fulfill(json=layout))
    page.goto(roadmap_url, wait_until="domcontentloaded")
    expect(page.locator("#roadmapError")).to_be_visible()
    expect(page.locator("#overview")).to_have_count(0)
    assert_no_injected_markup(page)


@pytest.mark.parametrize("fragment", ["constructor", "__proto__"])
def test_noncourse_hash_does_not_open_dialog(roadmap, roadmap_url, fragment):
    roadmap.goto("about:blank")
    roadmap.goto(roadmap_url + "#" + fragment, wait_until="domcontentloaded")
    expect(roadmap.locator("#catalogue tr")).to_have_count(29)
    expect(roadmap.locator("#detail")).to_be_hidden()
    expect(roadmap.locator("#roadmapError")).to_be_hidden()
