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
> **Project Created**: 2026-05-31

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

### `tests/test_example.py` ships a `TestCLI` suite for a non-existent `amc.cli` module

- **Priority**: High
- **Category**: Tooling
- **Discovered**: 2026-05-31

**Issue**: The generated `tests/test_example.py` includes a `TestCLI` class (12 tests) that
imports `from amc.cli import cli` and exercises a Click-based CLI (`hello`/`config` commands,
`--debug`, version option). The template never generates an `amc/cli.py` module, does not list
`click` as a dependency, and adds no `[project.scripts]` entry. As shipped, the project fails
12 tests immediately with `ModuleNotFoundError: No module named 'amc.cli'`, so a fresh clone
cannot pass its own test suite or the CI `pytest` gate.

**Context**: Discovered running the full suite while building out the FastAPI backend. The 12
failures reproduce on the initial commit (before any project code), confirming they are a
template defect rather than project regression. Because this project is a web app with no CLI
in scope, the stub was removed rather than satisfied.

**Suggested Fix**: Make the example test self-consistent with what the template generates.
Either (a) generate a minimal `src/{{package}}/cli.py` (Click group with `hello`/`config`),
add `click` to dependencies, and wire a `[project.scripts]` entry; or (b) gate the CLI test
block behind the same cookiecutter option that decides whether a CLI is scaffolded, so
non-CLI projects don't inherit tests for a module that was never created. Option (b) is
preferable for library/web-app project types.

**Affected Files**: `{{cookiecutter.project_slug}}/tests/test_example.py`,
`{{cookiecutter.project_slug}}/src/{{cookiecutter.package_name}}/` (missing `cli.py`),
`{{cookiecutter.project_slug}}/pyproject.toml` (dependencies, `[project.scripts]`).

---

### `.gitignore` `models/` rule silently swallows a `src/<pkg>/models/` package

- **Priority**: High
- **Category**: Configuration

**Issue**: The generated `.gitignore` contains an unanchored `models/` entry (under
"Data and models") intended for ML weight artifacts. Because it is unanchored, it also
matches `src/<package>/models/` - a very common name for an ORM/domain models package.
A newly added models package is silently untracked; `git add` appears to succeed but the
files never enter version control, which is easy to miss until CI fails to find the module.

**Context**: Discovered after adding a SQLAlchemy `src/amc/models/` package; `git status`
did not list it, and `git check-ignore -v` traced it to the `models/` line.

**Suggested Fix**: Anchor the ML artifact ignores to the project root (`/models/`,
`/weights/`, `/data/raw/`) so they cannot match nested source directories, and/or add an
explicit un-ignore (`!src/{{cookiecutter.package_name}}/models/`). Anchoring is the more
robust fix.

**Affected Files**: `{{cookiecutter.project_slug}}/.gitignore`.

---

### `.gitignore` Python `lib/` rule silently swallows `frontend/src/lib/`

- **Priority**: Critical
- **Category**: Configuration

**Issue**: The standard Python-build section of `.gitignore` lists unanchored directory
entries - `build/`, `lib/`, `lib64/`, `parts/`, `dist/`, etc. - meant for setuptools
artifacts that only ever appear at the repo root. Because they are unanchored, `lib/` also
matches `frontend/src/lib/` (a completely ordinary JS module directory: API client wrapper,
endpoints, query config, helpers). The whole directory was silently untracked - `git add`
reported success but the files never entered version control - so a fresh clone of the
frontend would not build (missing its entire API layer). Same failure mode as the `models/`
entry above, but higher impact because it hit load-bearing source. (`build/` and `dist/`
have the same latent collision with `frontend/build` / `frontend/dist`.)

**Context**: Discovered when `git add frontend/src/lib/cx.ts` printed "paths are ignored";
`git check-ignore -v` traced it to the unanchored `lib/` line. Several earlier frontend
commits had unknowingly omitted `frontend/src/lib/*`.

**Suggested Fix**: Anchor every directory entry in the Python-build block to the repo root
(`/build/`, `/lib/`, `/lib64/`, `/parts/`, `/dist/`, `/sdist/`, `/var/`, `/wheels/`, …) so
they cannot match nested source directories in `frontend/` or elsewhere. The `*.egg-info/`,
`*.egg`, `MANIFEST` glob entries are fine as-is.

**Affected Files**: `{{cookiecutter.project_slug}}/.gitignore`.

---

### Frontend scaffold ships unrendered `{{ cookiecutter.* }}` placeholders (build is broken)

- **Priority**: Critical
- **Category**: Tooling

**Issue**: The generated `frontend/` ships raw Jinja placeholders in source that the
post-gen hook never rendered: `frontend/src/App.tsx` (`{{ cookiecutter.project_name }}`,
`{{ cookiecutter.project_short_description }}`), `frontend/index.html` (title + description),
and `frontend/src/test/App.test.tsx` (which asserts on those literal placeholder strings). In
JSX, `<h1>{{ ... }}</h1>` parses as an object-literal child referencing an undefined
`cookiecutter` identifier, so `tsc -b` fails (TS1005/TS2304) and `vite build` is red on a fresh
clone. The committed test "passes" against the broken markup, masking it.

**Context**: Discovered building out the real frontend; `npm run build` failed immediately on
the placeholders, and `@vitejs/plugin-react-swc` also crashed vitest on the same file.

**Suggested Fix**: Ensure the cookiecutter post-gen step renders `frontend/**` (it appears to
render Python sources but skip the frontend), and replace the placeholder-asserting example
test with one that exercises real rendered UI.

**Affected Files**: `{{cookiecutter.project_slug}}/frontend/src/App.tsx`, `index.html`,
`src/test/App.test.tsx`; the cookiecutter post-gen hook.

---

### Frontend `useApi` hook is built for bearer/localStorage auth, incompatible with the cookie model

- **Priority**: High
- **Category**: Security

**Issue**: The scaffold's `frontend/src/hooks/useApi.ts` (axios) sends **no credentials**
(`withCredentials`/`credentials:'include'` absent) and instead reads `localStorage` for an
`auth_token` and sets an `Authorization: Bearer` header. For a template whose backend uses an
HTTP-only session cookie (the tech-spec/ADR-002 default here), this is doubly wrong: every
authenticated request goes out cookie-less (→ 401), and storing session material in
`localStorage` reintroduces the XSS token-theft exposure the HTTP-only cookie exists to avoid.
The default `apiClient` also reads `VITE_API_URL` and can be pointed cross-origin, which
silently breaks `SameSite=Lax` cookie auth.

**Context**: Discovered wiring the SPA to the cookie-authenticated API; the scaffold hook had
to be removed entirely and replaced with a generated typed client configured
`credentials:'include'` against a same-origin base.

**Suggested Fix**: Default the scaffold's API layer to `credentials:'include'` with a relative
same-origin base and no `Authorization`/`localStorage` handling; offer bearer-token wiring only
behind a cookiecutter option for projects that actually use token auth.

**Affected Files**: `{{cookiecutter.project_slug}}/frontend/src/hooks/useApi.ts`.

---

## Submitting Feedback

Once you've collected feedback, you can:

1. **Create an issue** in the [cookiecutter-python-template repository](https://github.com/ByronWilliamsCPA/cookiecutter-python-template/issues)
2. **Submit a PR** if you have fixes for the template
3. **Share this file** with the template maintainers

When submitting, reference this project as the source of the feedback.
