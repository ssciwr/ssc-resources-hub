# Repository instructions

This repository contains the public SSC Resources Hub and SSC AI Roadmap.

## Context

- Use [README.md](README.md) for environment setup, validation and preview commands.
- Read [ARCHITECTURE.md](ARCHITECTURE.md) before substantial frontend, schema or
  integration changes, and [CURRICULUM.md](CURRICULUM.md) before curriculum edits.
- Reuse the existing [contributor guide](docs/community/contribute-codebase.md).
  Prefer improving an existing module or workflow over adding standalone tooling.

## Scope and data

- Work on the public roadmap only. Keep internal tutor, training and creator
  materials outside this repository and its published assets.
- Curriculum JSON is authoritative. Preserve course content, learning outcomes,
  release selections and prerequisite semantics unless the user's request
  authorizes changing them. Do not infer instructor facts, dataset licenses or
  completed reviews from missing information.
- Audience categories guide recommendations, not eligibility. The two CLI courses
  are equivalent alternatives; learners need not complete both.
- Domain relationships belong in `data/dependencies.json`; SVG geometry belongs
  in `data/layout.json`. Keep their validation consistent.
- Preserve the established stack: MkDocs Material, Jinja/HTML, scoped CSS, ES
  modules, JSON/JSON Schema, SVG, Python/pytest, uv and GitHub Actions/Pages.
  New frameworks, a backend, database or npm build require explicit architectural
  approval.

## Working and verification

- Check Git status and preserve unrelated user changes. Prefer small, reviewable
  fixes to rewriting working components.
- Use uv and `uv.lock`; select the workspace `.venv/bin/python` in the editor.
  Follow the README commands rather than introducing another dependency workflow.
- For curriculum or schema changes, run validation and relevant non-browser
  tests. For frontend changes, run the browser regressions against a real MkDocs
  build. For documentation changes, check links and build the documentation.
- Keep dynamic content within the documented text, URL and SVG rendering policy.
  Update both validation and runtime protections when extending that policy.
- Automated validation checks structure and invariants. It does not certify
  licensing, exercise execution, teaching readiness or visual arrow routing.
- Report what was verified and what still needs author review. Generated output
  and caches are ignored; keep them out of source commits.
- Commit, push, merge or deploy only when authorized by the user. Authorization
  already given in the current task remains valid within its stated scope.
