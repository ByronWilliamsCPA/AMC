# Branch Consolidation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate three diverged branches into a single local working state with `main` current and the claude branch available locally for continued development.

**Architecture:** `origin/main` already contains all planning docs (from the squash-merged PR #1). `origin/claude/great-allen-WrIB9` has 23 implementation commits cleanly on top of `origin/main`. `docs/finalize-planning-frontend` is content-identical to `origin/main` and can be retired. No merge conflicts exist.

**Tech Stack:** git, bash

---

## Branch State Reference

| Branch | Commit | Notes |
|--------|--------|-------|
| `main` (local) | `1ef6223` | Behind `origin/main` by 1 commit |
| `origin/main` | `13e2ae1` | Squash-merge of planning PR #1 (17 files, +1406) |
| `docs/finalize-planning-frontend` | `f9aaa2b` | Empty diff vs `origin/main` - superseded |
| `origin/claude/great-allen-WrIB9` | `5a9ab8d` | 23 commits, 181 files, ~27 k lines of implementation |

---

### Task 1: Advance local `main` to match `origin/main`

**Files:**

- No file edits - git state change only

- [ ] **Step 1: Verify clean working tree**

```bash
git status
```

Expected: nothing to commit, working tree clean (the only untracked file is `.cruft.json`; that is fine).

- [ ] **Step 2: Switch to `main` and pull**

```bash
git checkout main
git pull origin main
```

Expected output includes:

```
Fast-forward
 docs/planning/PROJECT-PLAN.md | 349 ++++...
 ...
 17 files changed, 1406 insertions(+), 98 deletions(-)
```

- [ ] **Step 3: Confirm `main` is up to date**

```bash
git log --oneline -3
```

Expected first line: `13e2ae1 docs(planning): finalize plan, adopt React SPA frontend (#1)`

---

### Task 2: Create a local tracking branch for the claude implementation work

**Files:**

- No file edits - git state change only

- [ ] **Step 1: Check out the remote branch as a local tracking branch**

```bash
git checkout -b feat/implementation origin/claude/great-allen-WrIB9
```

The name `feat/implementation` follows the project branch naming convention (CLAUDE.md). Choose a different name if you prefer, but keep the `feat/` prefix and avoid spaces.

Expected:

```
Branch 'feat/implementation' set up to track remote branch 'claude/great-allen-WrIB9' from 'origin'.
Switched to a new branch 'feat/implementation'
```

- [ ] **Step 2: Confirm the branch tip and ancestry**

```bash
git log --oneline -5
```

Expected first line: `5a9ab8d docs(design): mark frontend build order complete`

Expected line 24 should be: `13e2ae1 docs(planning): finalize plan, adopt React SPA frontend (#1)`

Run to confirm the branch is cleanly on top of `main`:

```bash
git merge-base --is-ancestor main feat/implementation && echo "CLEAN" || echo "DIVERGED"
```

Expected: `CLEAN`

---

### Task 3: Install frontend dependencies so the working tree is ready

**Files:**

- `frontend/node_modules/` (generated, not tracked)

The claude branch added/changed `frontend/package.json` and `frontend/package-lock.json`. The `node_modules` directory does not exist on this branch yet.

- [ ] **Step 1: Install frontend dependencies**

```bash
cd frontend && npm ci && cd ..
```

`npm ci` uses the lock file exactly, ensuring reproducible installs. Expected: exits with code 0 and no peer-dependency errors.

- [ ] **Step 2: Install Python dependencies**

```bash
uv sync --all-extras
```

Expected: resolves from `uv.lock`, exits with code 0.

---

### Task 4: Verify the implementation is in a passing state

**Files:** (read-only verification, no edits)

- [ ] **Step 1: Run the backend test suite**

```bash
uv run pytest -x -q
```

Expected: all tests pass (97% coverage was the last recorded state on the claude branch - `2aa6766 test: raise coverage to 97%`).

- [ ] **Step 2: Run the frontend test suite**

```bash
cd frontend && npx vitest run && cd ..
```

Expected: all tests pass (vitest-axe a11y tests and component tests added by the claude branch).

- [ ] **Step 3: Run pre-commit on the full tree to confirm lint/format clean**

```bash
uv run pre-commit run --all-files
```

Expected: all hooks pass. If `markdownlint` or `no-em-dash` flags anything in the newly checked-out files, fix those before continuing.

---

### Task 5: Retire the superseded `docs/finalize-planning-frontend` branch

**Context:** `git diff origin/main..docs/finalize-planning-frontend` returns empty - all content from this branch is already in `origin/main`. Keeping the branch creates confusion about active workstreams.

- [ ] **Step 1: Delete the local branch**

```bash
git branch -d docs/finalize-planning-frontend
```

`-d` (safe delete) will succeed only if the branch is fully merged. If git refuses, re-check with `git diff origin/main..docs/finalize-planning-frontend` before using `-D`.

- [ ] **Step 2: Delete the remote tracking branch**

```bash
git push origin --delete docs/finalize-planning-frontend
```

Expected: `- [deleted]  docs/finalize-planning-frontend`

---

### Task 6: Confirm final branch state

- [ ] **Step 1: List all branches**

```bash
git branch -a
```

Expected result:

```
  main
* feat/implementation
  remotes/origin/main
  remotes/origin/claude/great-allen-WrIB9
  remotes/origin/feat/implementation
```

(The remote `claude/great-allen-WrIB9` will remain until explicitly deleted from GitHub - that is fine; leave it as provenance.)

- [ ] **Step 2: Verify `main` and `feat/implementation` ancestry**

```bash
git log --oneline --graph main feat/implementation | head -10
```

Expected: linear graph showing `feat/implementation` is ahead of `main` with no divergence.

---

## What You Have After This Plan

| State | Value |
|-------|-------|
| `main` | Current, matches `origin/main`, has all planning docs |
| `feat/implementation` | 23 commits of full-stack implementation ready to continue |
| `docs/finalize-planning-frontend` | Retired (content preserved in `origin/main`) |
| Python env | `uv sync` complete, all extras installed |
| Frontend env | `npm ci` complete, `node_modules` populated |
| Tests | Backend + frontend passing |

**Next step:** Continue feature development on `feat/implementation`, opening PRs against `main` per the project workflow.
