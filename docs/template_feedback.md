---
title: "Template Feedback"
schema_type: common
status: published
owner: core-maintainer
purpose: "Document template issues for upstream fixes."
tags:
  - feedback
  - template
---

> **Purpose**: Document issues discovered in this project that should be addressed in the [cookiecutter-python-template](https://github.com/ByronWilliamsCPA/cookiecutter-python-template).
>
> **Generated From**: cookiecutter-python-template v0.1.0
> **Project Created**: __PROJECT_CREATION_DATE__

---

## How to Use This File

When working on this project, if you discover any issue that originates from the template itself (not project-specific), add it here with the following format:

````markdown
### [Short Title]

- **Priority**: Critical / High / Medium / Low
- **Category**: [Configuration / Documentation / Tooling / Structure / CI/CD / Security / Other]
- **Discovered**: YYYY-MM-DD

**Issue**: [Clear description of what's wrong or missing]

**Context**: [How was this discovered? What were you trying to do?]

**Suggested Fix**: [What should the template do differently?]

**Affected Files**: [List template files that need changes]
````

---

## Feedback Items

<!-- Add your feedback below this line -->

### Planning-doc validator mis-resolves relative links in subdirectories

- **Priority**: Medium
- **Category**: Tooling
- **Discovered**: 2026-05-31

**Issue**: `scripts/validate-planning-docs.py` resolves every markdown link relative to
`docs/planning/` (the hardcoded `docs_dir`), ignoring the directory of the file that contains
the link. Consequences:

1. A link between two files inside `docs/planning/adr/` (for example ADR-002 linking to
   `./adr-001-initial-architecture.md`) is reported as a broken link, even though the path is
   correct on disk and renders correctly in MkDocs and on GitHub.
2. Conversely, `../`-prefixed links from an ADR up to `docs/planning/` (for example
   `../project-vision.md`) pass only by accident: the link regex strips one leading `.` and a
   `./` prefix, collapsing `../project-vision.md` to `project-vision.md`, which then resolves
   under `docs_dir`. So the check both false-flags valid sibling links and false-passes
   parent links.

**Context**: Discovered while adding `adr-002-frontend-framework.md` and cross-linking it with
`adr-001` during a `/project-planning` assumption-reconciliation pass. The links are correct;
the validator reports three spurious "Broken link" warnings.

**Suggested Fix**: Resolve each link relative to the containing file's parent directory
(`filepath.parent / link_path`) and then normalize with `.resolve()`, rather than always
joining to `docs_dir`. This handles `./`, `../`, and subdirectory links correctly and removes
the dot-stripping hack in the link regex.

**Affected Files**: `scripts/validate-planning-docs.py` (link extraction regex ~line 75 and
resolution ~lines 82-88).

### Unrendered `__PROJECT_CREATION_DATE__` placeholder in template_feedback.md

- **Priority**: Low
- **Category**: Configuration
- **Discovered**: 2026-05-31

**Issue**: The "Project Created" line in this file still reads
`__PROJECT_CREATION_DATE__`; the placeholder was never substituted during generation.

**Context**: Noticed while adding the first feedback item above.

**Suggested Fix**: Render the creation date from a cookiecutter/cruft context variable (the
project's actual creation date is 2026-05-31), or drop the line if no such variable exists.

**Affected Files**: `docs/template_feedback.md` (header, line 15).

### ADR template fails the repo's own front-matter validator (blocks all commits)

- **Priority**: Critical
- **Category**: Tooling
- **Discovered**: 2026-05-31

**Issue**: `docs/ADRs/adr-template.md` ships with front matter that the template's own
`validate-front-matter` pre-commit hook (`tools/validate_front_matter.py`) rejects on two
fields:

1. `schema_type: adr` is not a valid discriminator; the Pydantic models only accept
   `script`, `knowledge`, `planning`, or `common`.
2. Under a valid `schema_type`, `status: proposed` is rejected; the `planning` schema's
   `status` enum is `draft` / `in-review` / `published`. The template conflated the ADR
   decision-status vocabulary (proposed/accepted/superseded) with the doc-lifecycle status
   vocabulary.

Because that hook scans the whole `docs/` tree regardless of which files are staged, this
single template file fails the hook on **every** commit, blocking all commits in a freshly
generated repo until the file is hand-edited.

**Context**: Hit while running `pre-commit` before committing finalized planning documents.
The commit was blocked by `docs/ADRs/adr-template.md`, a file untouched by the change.

**Suggested Fix**: Either (a) ship `docs/ADRs/adr-template.md` with `schema_type: planning`
and `status: draft` so it passes out of the box, or (b) add a dedicated `adr` schema_type to
`tools/validate_front_matter.py` whose `status` enum is the ADR vocabulary
(proposed/accepted/superseded/deprecated). Option (b) better matches ADR semantics. Either
way, the shipped template must pass the shipped validator.

**Affected Files**: `docs/ADRs/adr-template.md`, `tools/validate_front_matter.py`.

---

## Submitting Feedback

Once you've collected feedback, you can:

1. **Create an issue** in the [cookiecutter-python-template repository](https://github.com/ByronWilliamsCPA/cookiecutter-python-template/issues)
2. **Submit a PR** if you have fixes for the template
3. **Share this file** with the template maintainers

When submitting, reference this project as the source of the feedback.
