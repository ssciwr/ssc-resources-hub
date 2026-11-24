# Scientific Software Center - Resource Hub

A dedicated resource hub for Heidelberg University researchers developing scientific software — offering structured guidelines, training, templates, and best practices to ensure reproducible, sustainable, and high-quality research outputs.


## Run this locally
1. Clone the repository 
```bash
git clone https://github.com/ssciwr/ssc-resources-hub.git
```

2. Retrieve all GitHub submodules
```bash
git submodule update --init --recursive
```

3. Install the locked documentation and test dependencies with uv
```bash
uv sync --locked --extra docs --group dev
```

4. Validate the curriculum and build the complete website
```bash
uv run --no-sync pytest tests/ai-roadmap -m "not browser" -q
uv run --no-sync mkdocs build
```

5. Run the MkDocs website locally
```bash
uv run --no-sync mkdocs serve
```

CI runs the same validation on pull requests and pushes to `main` or `master`.
Deployment runs only after validation succeeds on a push to one of those branches.
CI uses Python 3.13 and uv 0.11.32. The `docs` extra supplies MkDocs plugins;
the `dev` dependency group supplies test and maintenance tools. Development
dependencies use `--group dev`, replacing the former `dev` extra. `uv.lock` is the
single dependency lockfile. See the
[developer guide](docs/community/contribute-codebase.md#dependency-management)
for adding, removing, or updating dependencies.

## Curriculum validation

The tests validate the public AI Roadmap and exercise malformed copies of its
data. To check only the current curriculum, run:

```bash
uv run --no-sync python scripts/validate_ai_roadmap.py
```

The validator checks course and shared-data schemas, references, duplicate JSON
keys, prerequisite integrity, cycles, and diagram consistency. It preserves the
migration baseline of 29 courses (13 MVP and 16 future), five learning goals,
four audiences, and 35 relationships, including equivalent CLI alternatives,
AND prerequisites, recommendations, and conditional prerequisites. Intentional
curriculum extensions must update the baseline checks in
`scripts/validate_ai_roadmap.py` as part of their review.

The current frontend supports one OR group per course. Cycle detection includes
all relationship kinds, retaining the migration's conservative policy. Unassigned
instructors and unspecified practical projects remain valid draft placeholders;
when a project is supplied, its acceptance criteria are required too.

Conditional prerequisites use the `course` and `when` fields in
`docs/learn/ai-roadmap/data/dependencies.json`. The catalogue, prerequisite details,
and reverse "Enables" links read those records without course-specific frontend
rules. Diagram geometry and abbreviated labels remain in `data/layout.json`;
relationship changes must keep that layout and the reviewed baseline consistent.

Live summary counts and version labels come from the manifest, courses and
learning goals; audience controls and definitions share `data/audiences.json`.
The manifest's `equivalent_course_groups` records confirmed competency equivalence
for counting distinct MVP competencies. It is separate from prerequisite OR groups:
different valid routes into a subsequent course are not automatically equivalent.
Groups must contain existing course IDs and must not overlap. The migration
baseline declares only the two CLI courses as equivalent. Duration displays use
course duration caps, which still require timed delivery review.

Only declared public fields and listed data files are allowed. This guards
against accidental extra fields or files; it cannot determine whether prose in
an allowed field is confidential. Publication rights, teaching readiness, actual
SVG arrow geometry, and assistive-technology behavior require separate review.

Curriculum fields render as plain text, with escaped values in HTML attributes.
Bibliography citations additionally support balanced, attribute-free `<em>` tags;
the renderer builds those spans from text nodes rather than accepting general
HTML. Other citation markup fails validation and appears literally if validation
is bypassed. External links and avatars require complete HTTPS URLs without
embedded credentials, controls, quotes, or backslashes; invalid URLs are omitted.
Avatar errors use event listeners and retain the initials fallback.

The SVG renderer enforces a tag and attribute allowlist before mounting the map.
Colours use literal names or hexadecimal values, and markers reference local SVG
IDs. Script tags, event attributes, inline styles, and external paint references
fail validation and produce a visible load error if supplied directly to the
browser. New SVG features require a matching review of the schema and
`js/svg-policy.js`. These boundaries follow the context-specific approach in
[OWASP's XSS prevention guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

## Course specification gaps

Generate a contributor report from the validated curriculum:

```bash
uv run --no-sync python scripts/report_ai_roadmap_readiness.py
uv run --no-sync python scripts/report_ai_roadmap_readiness.py --mvp
```

Add `--json` for structured output. The report lists missing instructor assignments,
projects and acceptance criteria. It checks the existing data without writing any
files or changing course scope. Both CLI alternatives remain separate options.
It exits successfully for valid drafts even when fields remain incomplete.
Missing optional fields are prompts for author review, not additional schema
requirements or release gates.

Complete fields and material-coverage labels do not establish teaching readiness.
Exercise execution, dataset/model licensing, four-hour feasibility, project scope,
cross-cutting competencies and references need documented author review. Follow
the [course authoring guide](docs/community/contribute-codebase.md#ai-roadmap-course-specifications)
to supply confirmed content and review evidence.

## Browser regression tests

The browser suite uses [Playwright's pytest plugin](https://playwright.dev/python/docs/test-runners)
from the `dev` group. Install Chromium and its operating-system dependencies once:

```bash
uv run --no-sync playwright install --with-deps chromium
```

Run the browser suite:

```bash
uv run --no-sync pytest tests/ai-roadmap -m browser --browser chromium
```

Tests build the complete MkDocs site into a temporary directory and serve it on
localhost under `/ssc-resources-hub/`, exercising project-site asset paths. To
reuse a fresh existing build, add `--roadmap-site-dir site`. Curriculum and
browser tests can also be run together by omitting `-m browser` after installing
Chromium. Tests use the actual modules and JSON over HTTP; external services are
blocked, and avatar rendering uses deterministic responses. The multiple-profile
test reuses documented instructor information in test-only responses.

CI runs both suites before deployment, following Playwright's
[browser installation guidance](https://playwright.dev/python/docs/ci).
On browser failures, CI uploads traces and screenshots for seven days. To capture
the same artifacts locally, add `--tracing retain-on-failure --screenshot
only-on-failure --output test-results/ai-roadmap` to the pytest command.

For VS Code testing, select `.venv/bin/python` with **Python: Select
Interpreter**, then refresh test discovery. Select the executable, not the `.venv`
directory. Run `uv sync --locked --extra docs
--group dev` after test dependencies change. The workspace default interpreter
setting does not replace an already-selected Conda or other interpreter; see the
[VS Code interpreter settings](https://code.visualstudio.com/docs/python/settings-reference#general-python-settings).

## License

**MIT License**

Copyright (c) 2022-2025 Scientific Software Center

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
