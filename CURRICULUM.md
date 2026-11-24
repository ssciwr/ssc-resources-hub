# SSC AI Roadmap curriculum specification

These are the public curriculum's design constraints. Actual course content and
current labels live in [curriculum JSON](docs/learn/ai-roadmap/data); this document
does not duplicate the course catalogue or certify readiness to teach. Follow the
[course authoring guide](docs/community/contribute-codebase.md#ai-roadmap-course-specifications)
for contribution steps and evidence.

## Scope and baseline

The roadmap develops practical scientific competencies in understanding AI,
using AI in research, developing reliable software with AI, incorporating AI into
applications, and using, evaluating and deploying existing AI/ML models. Training
and fine-tuning models remain outside the current scope.

The initial v0.15 migration baseline is:

| Invariant | Value |
| --- | ---: |
| Learning goals | 5 |
| Course options | 29 |
| MVP / future course options | 13 / 16 |
| Curriculum relationships | 35 |
| Intended audience categories | 4 |
| Equivalent CLI learning options | 2 |

The [manifest](docs/learn/ai-roadmap/data/roadmap.json) records the curriculum
baseline separately from the application version. Approved extensions must
update data, relevant schemas, layout, baseline checks and documentation together.
The [validator](scripts/validate_ai_roadmap.py) enforces the current migration
baseline; it is not a reason to silently exclude approved future extensions.

## Goals, audiences and eligibility

The canonical [learning goals](docs/learn/ai-roadmap/data/learning-goals.json)
are LG-01 through LG-05. They are interconnected competencies, not sequential
stages. `F` denotes shared foundations and is not a sixth learning goal.

The [audience registry](docs/learn/ai-roadmap/data/audiences.json) defines Students,
Researchers, Academic Staff and Technical Professionals with inclusive
descriptions. Roles can overlap and determine recommendations, not eligibility.
Prerequisite competencies determine eligibility; equivalent prior competencies
are accepted without requiring course attendance.

## Course design

Each course has one primary objective, measurable outcomes, explicit
prerequisites and concise module descriptions. Teaching is practical,
scientifically oriented, local-first and open-source-oriented. Tools are chosen
for the competency rather than becoming unnecessary prerequisites.

The teaching cap is four hours. Practical projects, where planned, are limited
to two small projects with acceptance criteria. Exercises need reproducible
instructions and appropriately licensed resources. Bibliography entries are
course-specific IEEE references, reused through the central registry. Multiple
instructors are supported, with confirmed profiles and initials fallback.

Responsible AI, security and privacy, evaluation and validation, and
reproducibility are mandatory cross-cutting competencies. Authors must connect
them to actual activities and checks; the presence of the UI banner alone does
not demonstrate coverage.

## Relationships and equivalence

Relationships are independent of diagram geometry and are declared in
[`dependencies.json`](docs/learn/ai-roadmap/data/dependencies.json).

| Field | Competency meaning |
| --- | --- |
| `all_of` | All listed competencies are required: AND. |
| `any_of` | At least one listed competency in the group is required: OR. The current implementation accepts one group per target. |
| `recommended` | Preparation guidance, not an eligibility requirement. |
| `conditional` | An additional competency applies when the described variant or circumstance is selected. |

Mandatory and alternative requirements combine. Applicable conditional
requirements are additional; they do not make the condition apply to every
learner. The `when` value is explanatory text, not an executable eligibility rule.

Claude Code CLI and Codex CLI are independent, equivalent learning alternatives.
A learner can choose either without completing both. The manifest records their
equivalence for competency counts, while dependency OR groups represent the
permitted routes into subsequent courses. An OR group with other courses does
not, by itself, declare those courses equivalent.

## Draft status and review evidence

[`course.schema.json`](schemas/course.schema.json) defines the supported course
fields. Unassigned instructors and absent project specifications remain valid
draft states; projects and acceptance criteria are paired when specified.
The optional [draft report](scripts/report_ai_roadmap_readiness.py) identifies
missing fields and keeps both CLI options separate.

Material-coverage labels indicate potential reuse, and `duration_minutes` is a
teaching cap. Neither establishes a successful delivery trial. The current data
model does not track exercise execution, licensing or delivery-review evidence.
Authors supply that evidence in exercise documentation and the review process,
as described in the contribution guide. Public references are not a substitute
for confirming reuse rights. Keep internal tutor material outside public assets.
