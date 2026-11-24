# SSC AI Roadmap architecture

The public roadmap is a static, data-driven application inside the existing
MkDocs Material site. This document describes the current implementation; setup
and commands remain in [README.md](README.md), and curriculum rules are in
[CURRICULUM.md](CURRICULUM.md).

## Integration and data flow

[`mkdocs.yml`](mkdocs.yml) adds the roadmap to navigation and sets the production
site URL. The [page entry](docs/learn/ai-roadmap/index.md) selects the
[Jinja template](material/overrides/ai-roadmap.html), which includes the shared
[HTML fragment](material/overrides/partials/ai-roadmap-content.html). The standalone
[preview script](scripts/preview_ai_roadmap.py) uses that same fragment.

The template loads the roadmap's scoped stylesheet and ES module entry point.
JSON is fetched relative to the module URL, so assets work beneath the GitHub
Pages repository prefix as well as in local previews. There is no dedicated
backend, database or npm build step. The application does not track completed
courses or make automated eligibility decisions. External fonts and instructor
avatars can require network access.

The [data directory](docs/learn/ai-roadmap/data) holds the manifest, independent
course specifications, learning goals, audiences, dependencies, bibliography,
instructors and layout. Bibliography and instructor IDs are reusable references.
These files are published as static assets; an unused field is still public.

## Frontend responsibilities

All paths in this table are relative to `docs/learn/ai-roadmap/js/`.

| Module | Responsibility |
| --- | --- |
| `main.js`, `app.js` | Report startup failures and connect component behavior. |
| `data-loader.js` | Load the manifest and JSON records; resolve instructor IDs and expose domain data. |
| `dependencies.js` | Query mandatory, alternative, recommended and conditional relationships in both directions. |
| `graph.js`, `svg-policy.js` | Construct the approved SVG, enforce its rendering boundary, highlight nodes and control zoom. |
| `filters.js` | Audience picker, goal selection, search precedence and reset. |
| `catalogue.js` | Filtered course rows and prerequisite summaries. |
| `course-dialog.js` | Course details, prerequisite navigation, instructor fallback and bibliography. |
| `metadata.js` | Dataset-wide counts, versions, duration caps and audience definitions. |
| `dom.js` | Scoped DOM access, text escaping, URL checks and limited citation formatting. |

The [stylesheet](docs/learn/ai-roadmap/css/roadmap.css) is scoped beneath
`.ssc-roadmap`; page-specific Material layout adjustments live in the Jinja
template. Content changes should normally affect JSON rather than frontend code.

## Interaction contracts

- Keep one unified diagram with all learning paths and one node per course.
  Filters dim diagram nodes while filtering catalogue rows; dimmed courses remain
  available to open.
- Search examines the complete curriculum and overrides goal/audience filters.
  Their values remain selected and resume taking effect when search is cleared.
- Audience help and definitions share the audience registry. Summary counts
  describe the full dataset, not the filtered results.
- Dialogs show prerequisites first. Within-dialog navigation moves focus to the
  new title; closing the native dialog restores focus to its opening control.
- Conditional wording and reverse links come from dependency records. Confirmed
  course equivalence is separate from alternative prerequisite routes.
- Preserve zoom, actual-size and fit controls. External prerequisites belong in
  course details rather than the main diagram.

## Layout and rendering boundaries

[`layout.json`](docs/learn/ai-roadmap/data/layout.json) stores manually routed SVG
elements, course IDs and abbreviated labels. It is not an automatic routing
engine. Dependency changes require corresponding layout changes; long course
renames also need a visual label review.

The [schemas](schemas) and [validator](scripts/validate_ai_roadmap.py) check
references, node multiplicity and relationship metadata. They do not establish
that polyline coordinates meet the intended rectangles or avoid crossings.

The [rendering policy](README.md#curriculum-validation) covers plain text,
citations, external URLs and allowed SVG. Runtime protections are intentional
even though CI validates the data. A structural public-field allowlist cannot
determine whether prose in an allowed field is confidential.

## Validation and delivery

The [workflow](.github/workflows/ci_mkdocs.yaml) installs locked dependencies,
runs non-browser tests, builds MkDocs, and runs Chromium regressions before the
deployment job. Deployment is restricted to successful pushes on the configured
main branches. Agent actions still require the authorization described in
[AGENTS.md](AGENTS.md).

Browser tests serve the actual build under the repository URL prefix and check
local asset failures and JavaScript errors. External services are blocked;
specific JSON responses and avatars are replaced only for test cases that need
them. Failure traces and screenshots are retained by CI.

The current dependency cycle check includes all relationship kinds. This is a
conservative integrity rule, not a declaration that recommended or conditional
courses are always mandatory. Current prerequisite rendering supports one OR
group per target; expanding it requires coordinated schema, UI and test changes.

Record future substantial architectural decisions with their context, options,
decision and consequences when an ADR would add useful rationale. Routine
content edits can use the existing specifications and contribution guide.
