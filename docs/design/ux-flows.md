---
title: "AMC Trainer - UX Flows, IA & Wireframes"
schema_type: design
status: draft
owner: ux
purpose: "Implementation-ready UX flows, information architecture, and wireframes for the AMC Trainer web app."
tags:
  - design
  - ux
  - wireframes
  - information-architecture
component: Frontend
---

> **Status**: Draft for engineering | **Version**: 1.0 | **Updated**: 2026-05-31

## TL;DR

This document defines the UX for **AMC Trainer**: a private, invite-only web app where a
math coach (staff) and up to ~30 students take timed AMC 8/10/12 practice contests and AoPS
placement diagnostics, then receive a synthesized starting-course recommendation. It covers
the information architecture, the four core journeys, a labeled wireframe for every screen,
the loading/empty/error/success states, and the microcopy.

**Design is grounded in what already exists** under `frontend/src/` (routes in `App.tsx`,
components under `features/` and `pages/`) and the **exact** API response shapes in
`docs/api/openapi.json`. Where a wireframe adds something the code does not yet have (a
confirm-submit dialog, a low-time warning, a coach roster), it is called out explicitly as a
**[NEW]** refinement, and the open decisions are collected in
[Section 8: Open UX questions](#8-open-ux-questions).

### Locked design constraints

| Constraint | Decision |
|------------|----------|
| Visual tone | **Clean & academic** — calm, focused, exam-serious, high legibility. No decorative chrome; generous whitespace; restrained color (color never the sole status carrier). |
| Styling | **CSS Modules + design tokens.** Tokens (owned by a teammate) are referenced abstractly here: `primary accent`, `surface`, `surface-raised`, `text`, `muted-text`, `success`, `danger`, `warning`, `border`, `focus-ring`. No hex values in this doc. |
| Auth (v1) | **Invite-only email/password with server-side sessions** (HTTP-only `amc_session` cookie). Authentik SSO is a documented future option; the Login screen is kept minimal so swapping the credential form for an SSO "Sign in" button is trivial (see [2.1](#21-login)). |
| Math rendering | KaTeX via the existing `Tex` component (`frontend/src/components/Tex.tsx`). |
| The hard rule | **Answer keys never leak pre-submission.** `ExamDetail` / `ProblemRead` carry no `correct_answer`; `DiagnosticItemRead` carries no `answer`. Keys appear **only** in the graded review returned by the attempt POST. This single constraint is why the **runner** (key-free) and the **review** (key-bearing) are separate screens that never coexist. |

---

## 1. Information Architecture & Navigation

### 1.1 Route map

All authenticated screens render inside the app shell (`Layout`, persistent header nav).
`/login` and `/register` render standalone (no nav), since the user has no session yet.

```text
PUBLIC (no session, no app shell)
  /login                         Sign in (email + password)
  /register?token=<token>        Invite redemption -> account creation

AUTHENTICATED (app shell + role-aware nav; guarded by RequireAuth)
  /                              -> redirects to /exams
  /exams                         Practice-test catalog (contest filter)
  /exams/:examId                 Exam runner  (timed)  ──submit──► graded review (same route)
  /diagnostics                   Diagnostic catalog
  /diagnostics/:instrumentId     Diagnostic runner ──submit──► verdict result (same route)
  /progress                      My progress dashboard (recommendation + history)

STAFF ONLY (coach / admin; RequireAuth staffOnly -> non-staff redirected to /)
  /users/:userId/progress        A student's progress (read-only, coach view)
  /invite                        Mint a one-time invite
```

Notes that match the current router (`frontend/src/App.tsx`):

- `index` redirects to `/exams` (the app "home" is the test catalog, since taking tests is
  the primary job).
- Unknown paths (`*`) redirect to `/` and then to `/exams`.
- Feature routes are lazy-loaded; the runner pulls in KaTeX, so it loads on demand. Plan for
  a brief route-level `Spinner` (label `"Loading…"`) on first navigation to a heavy route.

### 1.2 Primary navigation (role-aware)

The header (`Layout`) is a single horizontal bar: brand on the left, primary nav center-left,
user identity + sign-out on the right. It is **the same shell for all roles**; staff simply
see one extra link.

**Student nav**

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  AMC Trainer        Tests   Diagnostics   Progress              Bayden  [Sign out] │
└──────────────────────────────────────────────────────────────────────────────┘
       brand            └──── primary nav (NavLink) ────┘        display_name   button
```

**Coach / admin nav** (adds **Invite**; `isStaff` = role ∈ {coach, admin})

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  AMC Trainer    Tests   Diagnostics   Progress   Invite          Coach  [Sign out] │
└──────────────────────────────────────────────────────────────────────────────┘
                                                   ▲ staff-only
```

- The active route gets an underline/weight treatment via `NavLink`'s active state (color +
  a 2px `primary accent` underline so it is not color-only).
- `/users/:userId/progress` is **not** a top-level nav item — a coach reaches it by drilling
  in from a student roster. **[NEW]** The current build has no roster UI, so a coach cannot
  yet navigate to a student. See [4.2](#42-coach-journey-mint-an-invite-view-a-students-progress)
  and [Open question Q7](#8-open-ux-questions).
- **Mobile (< ~640px):** the brand stays; the three/four nav links collapse under a "Menu"
  disclosure (hamburger) that expands a vertical list; the user identity + Sign out move to
  the bottom of that expanded panel. Keep it a plain disclosure, not an animated drawer
  (academic, calm).

### 1.3 Role & access model (what each role sees)

| Capability | Student | Coach / Admin |
|------------|:-------:|:-------------:|
| Take tests & diagnostics | yes | yes |
| See **own** progress (`/progress`) | yes | yes |
| See **another** student's progress (`/users/:id/progress`) | no (403 → redirect home) | yes |
| Mint invites (`/invite`) | no (nav hidden + route redirect) | yes |

`RequireAuth` enforces this client-side (unauth → `/login` preserving `from`; non-staff on a
staff route → `/`); the server enforces it for real (403 `AuthorizationError`). The UI must
treat a server 403 as authoritative even if the client guard was bypassed.

---

## 2. Auth screens

### 2.1 Login

`/login` — standalone, centered card on a calm `surface` background. Matches `LoginPage.tsx`.

```text
                     ┌─────────────────────────────────────────┐
                     │                                         │
                     │              AMC Trainer                │   ← wordmark (brand)
                     │                                         │
                     │   Sign in                               │   ← h1
                     │                                         │
                     │   Email                                 │
                     │   ┌─────────────────────────────────┐   │
                     │   │ you@example.com                 │   │   autocomplete=username
                     │   └─────────────────────────────────┘   │
                     │                                         │
                     │   Password                              │
                     │   ┌─────────────────────────────────┐   │
                     │   │ ••••••••••                       │   │   autocomplete=current-password
                     │   └─────────────────────────────────┘   │
                     │                                         │
                     │   [ ⚠ Invalid email or password. ]      │   ← role="alert", only on error
                     │                                         │
                     │   ┌─────────────────────────────────┐   │
                     │   │            Sign in              │   │   ← primary; "Signing in…" while busy
                     │   └─────────────────────────────────┘   │
                     │                                         │
                     │   Have an invite? Set up your account → │   ← link to /register
                     └─────────────────────────────────────────┘
```

- **SSO-readiness (locked decision):** the credential `<form>` lives in one self-contained
  block. To later add Authentik SSO, drop a single **"Sign in with SSO"** button above (or in
  place of) this form — the surrounding card, heading, and centering do not change. Keep a
  visual slot reserved between the `h1` and the Email field so the SSO button can be inserted
  without relayout.
- Already-authenticated users hitting `/login` are redirected to `/` (no flash of the form).

**States**

| State | Behavior / copy |
|-------|-----------------|
| Default | Empty fields; Sign in enabled. |
| Submitting | Button label → `Signing in…`, button disabled. |
| Error 401 | `role="alert"`: **"Invalid email or password."** Fields retain input; password not cleared automatically (user can retry). |
| Error other | **"Could not sign in. Please try again."** |
| Rate-limited | Login is rate-limited per email server-side; surface the generic **"Could not sign in. Please try again."** (do not reveal lockout specifics — avoids account enumeration). Consider copy **"Too many attempts. Wait a minute and try again."** if the API distinguishes it — see [Q8](#8-open-ux-questions). |

### 2.2 Register (invite redemption)

`/register?token=<token>` — standalone. Reads `token` from the query string, validates it via
`GET /api/v1/auth/invites/{token}` for display, then `POST /api/v1/auth/register` creates the
account and the server sets the session cookie. Matches `RegisterPage.tsx`.

**Valid invite:**

```text
                     ┌─────────────────────────────────────────┐
                     │   Set up your account                   │   ← h1
                     │                                         │
                     │   Creating an account for               │   ← from invite (read-only)
                     │   bayden@example.com                    │
                     │                                         │
                     │   Display name                          │
                     │   ┌─────────────────────────────────┐   │
                     │   │ Bayden                          │   │
                     │   └─────────────────────────────────┘   │
                     │                                         │
                     │   Password (8+ characters)              │
                     │   ┌─────────────────────────────────┐   │
                     │   │ ••••••••••                       │   │   minLength=8, new-password
                     │   └─────────────────────────────────┘   │
                     │                                         │
                     │   ┌─────────────────────────────────┐   │
                     │   │         Create account          │   │   ← "Creating…" while busy
                     │   └─────────────────────────────────┘   │
                     │                                         │
                     │   Already set up? Sign in →             │
                     └─────────────────────────────────────────┘
```

**Invalid / missing / expired invite** (no token, or `valid:false`):

```text
                     ┌─────────────────────────────────────────┐
                     │   Set up your account                   │
                     │                                         │
                     │   ⚠ This invite link is invalid or has  │   ← role="alert"
                     │     expired. Ask your coach for a new   │
                     │     one.                                │
                     │                                         │
                     │   Already set up? Sign in →             │   ← always offered
                     └─────────────────────────────────────────┘
```

**States**

| State | Behavior / copy |
|-------|-----------------|
| Validating token | Brief check on mount; render nothing form-side until `valid` resolves (avoid a flash of the form then an error). A `Spinner` (`"Checking your invite…"`) is acceptable if validation is slow. |
| Valid | Show form, pre-fill nothing but display the invite email. |
| Invalid/expired/missing | Show the alert above; **hide the form** (cannot register). |
| Submitting | Button → `Creating…`, disabled. |
| Error 422 (weak password) | **"Password must be at least 8 characters."** |
| Error other (used/invalid invite at submit) | **"Could not create your account. The invite may be invalid or used."** |
| Success | Server sets cookie; redirect to `/` → `/exams`. (First login lands the student directly in the test catalog.) |

---

## 3. The exam experience (the heart of the app)

The exam splits into two screens on **one route** (`/exams/:examId`): the **runner** (no key)
and, after submit, the **review** (key revealed). They never coexist — this enforces the
answer-key constraint.

### 3.1 Exam list (`/exams`)

Catalog of papers with a contest filter (`All / AMC 8 / AMC 10 / AMC 12`), querying
`GET /api/v1/exams?contest=`. Matches `ExamListPage.tsx`; each row uses `ExamSummary`
(`contest`, `year`, `variant`, `num_problems`, `duration_sec`, `score_mode`).

```text
┌── app shell header ───────────────────────────────────────────────────────────┐
│  AMC Trainer    Tests   Diagnostics   Progress   (Invite)        Name [Sign out]│
└────────────────────────────────────────────────────────────────────────────────┘

  Practice tests                                                            ← h1

  Filter by contest:  [ All ]  [ AMC 8 ]  [ AMC 10 ]  [ AMC 12 ]            ← aria-pressed
                        ▲ active button gets filled/underlined treatment

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  AMC 10 2022A  ·  25 problems  ·  75 min  ·  6-point               →      │
  ├──────────────────────────────────────────────────────────────────────────┤
  │  AMC 10 2021B  ·  25 problems  ·  75 min  ·  6-point               →      │
  ├──────────────────────────────────────────────────────────────────────────┤
  │  AMC 8  2023   ·  25 problems  ·  40 min  ·  count                 →      │
  └──────────────────────────────────────────────────────────────────────────┘
        ↑ each row is a Link to /exams/:examId; whole row is the click target
```

**[NEW] refinement vs. current build:** the current list shows only
`"{contest} {year}{variant} — {num_problems} problems"`. Add **duration** (from
`duration_sec`, formatted `75 min`) and a plain-language **score mode** label
(`sixpoint → "6-point"`, `count → "count"`), so a student knows the time commitment and
scoring before committing. These fields are already in `ExamSummary`.

**States**

| State | Copy / behavior |
|-------|-----------------|
| Loading | `Spinner` — **"Loading tests…"** |
| Error | `ErrorState` — **"Could not load tests"** |
| Empty (`[]`) | `EmptyState` — **"No tests available yet."** |
| Success | The list above. |

### 3.2 Exam runner (`/exams/:examId`) — the centerpiece

Loads `ExamDetail` (key-free `problems[]`, each a `ProblemRead`). State lives in the
`runnerState` reducer (`answers`, `flags`, `current`, `phase`); the timer is the
absolute-deadline `useCountdown` that auto-submits once at zero. Matches `ExamRunnerPage.tsx`
+ `Palette` + `Question`.

**Desktop layout** — header (title · timer · progress), then a two-column body: palette
navigator on the left, the current problem + controls on the right.

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│  AMC 10 2022A                      ⏱ 1:04:12                12 of 25 answered     │  ← header
│  (contest year+variant)            role="timer"            aria-live=polite       │
├──────────────────┬─────────────────────────────────────────────────────────────┤
│  QUESTION         │   Problem 13                                                  │
│  NAVIGATOR        │                                                              │
│                   │   ┌──────────────────────────────────────────────────────┐  │
│  ┌──┬──┬──┬──┬──┐ │   │  A regular hexagon has area 24√3.  What is the        │  │
│  │ 1│ 2│ 3│ 4│ 5│ │   │  length of one side?           (KaTeX / image)        │  │
│  ├──┼──┼──┼──┼──┤ │   └──────────────────────────────────────────────────────┘  │
│  │ 6│ 7│ 8│ 9│10│ │                                                              │
│  ├──┼──┼──┼──┼──┤ │   ( ) A   2√2                                                 │
│  │11│12│13│14│15│ │   ( ) B   2√3        ◄ radiogroup, A–E, one per row          │
│  ├──┼──┼──┼──┼──┤ │   (•) C   4          ◄ selected                              │
│  │16│17│18│19│20│ │   ( ) D   4√2                                                 │
│  ├──┼──┼──┼──┼──┤ │   ( ) E   4√3                                                 │
│  │21│22│23│24│25│ │                                                              │
│  └──┴──┴──┴──┴──┘ │   Clear answer                ◄ link-button, only if selected │
│                   │                                                              │
│  Legend:          │   ┌──────────┬────────┬────────┬──────────────────────────┐ │
│  ▦ answered       │   │ Previous │  Flag  │  Next  │        Submit            │ │
│  ⚑ flagged        │   └──────────┴────────┴────────┴──────────────────────────┘ │
│  ▣ current        │     disabled        toggles      disabled       primary      │
│  ░ voided         │     on Q1          (aria-         on last                    │
│                   │                     pressed)                                  │
└──────────────────┴─────────────────────────────────────────────────────────────┘
```

**Palette cell semantics** (from `Palette.tsx`) — status is conveyed by **text +
shape/border, never color alone** (accessibility rule the codebase follows):

| Cell | Visual | `aria-label` |
|------|--------|--------------|
| Unanswered | plain `surface`, thin `border` | `Question N: unanswered` |
| Answered | filled `surface-raised`, heavier border | `Question N: answered` |
| Flagged | shows a `⚑` glyph + edge marker (combinable with answered) | `Question N: answered, flagged` |
| Current | thick `primary accent` ring, `aria-current="true"` | (label as above) |
| Voided | muted/hatched, still selectable to view | `Question N: voided` |

**Header timer:** `role="timer"`, label `Time remaining: M:SS` (or `H:MM:SS` past an hour, via
`formatDuration`). `aria-live="off"` on the ticking value so it does not spam a screen reader
every second.

**Controls (exact behavior, from the reducer):**

- **Previous / Next** — move `current`; Previous disabled at Q1, Next disabled at last problem.
- **Flag** — toggles `flags[current]`; `aria-pressed`; label flips **Flag ⇄ Unflag**.
- **Submit** — fires the single guarded submit; label → `Submitting…` while in flight.
- **Choices** — A–E radiogroup; selecting sets the answer; **Clear answer** (link-button)
  appears only when a choice is selected and removes it (back to blank).
- Once `phase` leaves `active` (submitting/review), answers/flags freeze (`disabled`).

**[NEW] refinements layered onto the runner** (the current build omits these; they are the
main UX gaps — see [Open questions](#8-open-ux-questions)):

1. **Low-time warning.** At **5:00 remaining**, give the timer a non-color emphasis (bold +
   a `⚠` glyph + an `aria-live="assertive"` one-shot announcement **"5 minutes remaining."**).
   At **1:00**, repeat once: **"1 minute remaining."** Recommended default: **on** (Q3).
2. **Confirm-before-submit dialog** when the user clicks **Submit manually** (auto-submit at
   zero must NOT confirm — there is no time to). Recommended default: **confirm only if
   blanks remain** (Q1). Dialog wireframe:

```text
        ┌───────────────────────────────────────────────┐
        │  Submit your test?                            │
        │                                               │
        │  You have 3 unanswered problems (and 2        │   ← derived from answers/flags
        │  flagged). Once you submit, you can't change   │
        │  your answers.                                │
        │                                               │
        │            [ Keep working ]   [ Submit ]      │   ← Submit = primary/danger-ish
        └───────────────────────────────────────────────┘
```

   - If no blanks and no flags: copy simplifies to **"Once you submit, you can't change your
     answers."** (or skip the dialog entirely per Q1).
   - Focus moves into the dialog; `Esc` / "Keep working" returns to the runner unchanged.

3. **Auto-submit-at-zero moment.** When the deadline passes, the runner submits automatically
   (no dialog). Show a brief inline, non-blocking notice as the review loads:
   **"Time's up — submitting your test."** Then the review replaces the runner. Because submit
   is guarded, a manual click landing at the same instant cannot double-submit; a server
   **409** is treated as "already submitted" and also lands on review.

**Runner states**

| State | Copy / behavior |
|-------|-----------------|
| Loading exam | `Spinner` — **"Loading exam…"** |
| Load error / not found (404) | `ErrorState` — **"Could not load this exam"** with a link back to `/exams`. |
| Active | The runner above; timer ticking. |
| Submitting | Submit → `Submitting…`; controls frozen; auto-submit path shows the "Time's up" notice. |
| Submit error (network, not 409) | Non-destructive inline `ErrorState` — **"Could not submit. Your answers are still here — try again."** Re-enable Submit so the student can retry (do **not** discard answers). |
| Submit conflict (409) | Treat as already submitted → go to review (fetch latest if needed). |
| Reviewed | Replaced by [3.3 Exam review](#33-exam-review-graded). |

**Mobile / stacked variant (runner).** The two-column body collapses to a single column:

```text
┌───────────────────────────────────────────┐
│ AMC 10 2022A         ⏱ 1:04:12             │  ← header stays sticky at top
│ 12 of 25 answered                          │
├───────────────────────────────────────────┤
│ [ ▸ Questions (12/25) ]                    │  ← palette collapses to a disclosure
├───────────────────────────────────────────┤   (expands the number grid inline)
│ Problem 13                                 │
│ ┌───────────────────────────────────────┐ │
│ │ … prompt (KaTeX / image, scrolls) …   │ │
│ └───────────────────────────────────────┘ │
│ ( ) A …   (•) C …   ( ) E …                │  ← choices stack full-width
├───────────────────────────────────────────┤
│  ◀ Prev    ⚑ Flag    Next ▶    [ Submit ]  │  ← controls become a sticky bottom bar
└───────────────────────────────────────────┘
```

- Timer stays pinned (sticky header) so it is always visible while scrolling a long problem.
- Palette is a collapsible disclosure showing the answered count in its label; tapping a cell
  jumps and auto-collapses.
- Controls become a **sticky bottom action bar** (thumb-reachable).
- Problem images: constrain to viewport width, allow pinch-zoom (do not lock scaling).

### 3.3 Exam review (graded)

The **only** screen that shows correct answers. Renders `ExamResultResponse`: score breakdown
(`score`, `max_score`, `correct`, `wrong`, `blank`) + a per-problem table from `review[]`,
each item `{ n, your, correct, ok, voided }`. Matches `ExamReview.tsx`.

```text
  Your result                                                              ← h2, aria-live

  ┌────────────┬───────────┬───────────┬───────────┐
  │  Score     │  Correct  │  Wrong    │  Blank    │
  │  105 / 150 │    17     │     6     │     2     │      ← <dl> score summary
  └────────────┴───────────┴───────────┴───────────┘

  Per-problem review                                                       ← <caption>
  ┌─────┬───────────────┬───────────┬─────────────┐
  │  #  │  Your answer  │  Correct  │  Outcome    │
  ├─────┼───────────────┼───────────┼─────────────┤
  │  1  │      C        │     C     │  Correct    │   ok=true
  │  2  │      —        │     B     │  Incorrect  │   your=null → "—"
  │  3  │      D        │     A     │  Incorrect  │
  │  …  │      …        │     …     │     …       │
  │ 11  │      —        │     C     │  Void       │   voided=true → "Void" (excluded from score)
  └─────┴───────────────┴───────────┴─────────────┘

  [ Back to tests ]            [ View my progress ]            ← [NEW] next-step actions
```

- **Outcome** mapping (from code): `voided → "Void"`; else `ok ? "Correct" : "Incorrect"`.
  Reinforce with a non-color glyph per row (✓ / ✗ / —) so outcome is not color-only.
- `your` is `null` for blanks → render **"—"**.
- On submit success the code already invalidates the progress query, so the dashboard reflects
  this attempt immediately.
- **[NEW]** Add two footer actions — **"Back to tests"** (`/exams`) and **"View my
  progress"** (`/progress`) — so the review is not a dead end. Optionally surface
  `solution_url` per row as a **"Solution"** link if present (the data model has it; the
  current `ReviewItemResponse` does not yet expose it — flag as [Q6]).
- **States:** review only renders on a successful submit, so it has no independent
  loading/empty/error of its own; its error is the runner's submit error above.
- **Mobile:** the score `<dl>` wraps to a 2×2 grid; the table becomes horizontally scrollable
  within its container (keep `#`, `Outcome` visible; let `Your`/`Correct` scroll) — or, for
  the academic-calm feel, render each problem as a stacked row card (`# 2 · your — · correct B
  · Incorrect`).

---

## 4. The diagnostic & placement experience

### 4.1 Diagnostic list (`/diagnostics`)

Lists the AoPS instruments from `GET /api/v1/diagnostics` (`DiagnosticSummary`: `id`,
`course`, `kind`, `role`). Matches `DiagnosticListPage.tsx`.

```text
  Placement diagnostics                                                    ← h1

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  Prealgebra 1  —  Are You Ready?                                   →      │
  ├──────────────────────────────────────────────────────────────────────────┤
  │  Prealgebra 1  —  Do You Know?                                     →      │
  ├──────────────────────────────────────────────────────────────────────────┤
  │  Introduction to Algebra B  —  Are You Ready?                      →      │
  │  …                                                                        │
  └──────────────────────────────────────────────────────────────────────────┘
       ↑ Link to /diagnostics/:instrumentId; label = "{course} — {kind}"
```

**[NEW] optional grouping:** there are 10 instruments spanning several courses, each with an
"Are You Ready?" (AYR) and/or "Do You Know?" (DYK) role. Grouping rows by `course` with the
`kind` as the secondary label improves scannability. Low effort; nice-to-have.

**States**

| State | Copy / behavior |
|-------|-----------------|
| Loading | `Spinner` — **"Loading diagnostics…"** |
| Error | `ErrorState` — **"Could not load diagnostics"** |
| Empty | `EmptyState` — **"No diagnostics available yet."** |
| Success | The list above. |

### 4.2 Diagnostic runner (`/diagnostics/:instrumentId`)

Loads `DiagnosticDetail` (`instructions` + key-free `items[]`, each `DiagnosticItemRead` with
`section_title`, `label`, `prompt`, **`manual`**). The `manual` flag is the pivotal UX
distinction: **auto-graded** items take a typed text answer; **manual** (symbolic) items are
worked on paper and **self-marked** with a checkbox. Submits `{responses, marks, elapsed_sec}`.
Matches `DiagnosticRunnerPage.tsx`.

```text
  Introduction to Algebra B — Are You Ready?                               ← h1 (course)

  ┌────────────────────────────────────────────────────────────────────────────┐
  │  Work each problem on paper. Type your answer where there's a box; for       │  ← instructions
  │  problems marked "self-mark," check the box if your written solution is      │     (from API)
  │  correct.                                                                    │
  └────────────────────────────────────────────────────────────────────────────┘

  ── Fundamentals ───────────────────────────────  ◄ section_title (group header) [NEW]

  1.  Evaluate  3x + 5  when  x = 4.                          ← prompt (KaTeX via Tex)
      Your answer:  ┌──────────────────┐                     ← auto: text input
                    │ 17               │
                    └──────────────────┘

  2.  Simplify  (2/3) ÷ (4/9).                                ← auto item
      Your answer:  ┌──────────────────┐
                    │ 3/2              │                       ← accepts 3/2, 1 1/2, etc. (server parses)
                    └──────────────────┘

  ── Problem solving ────────────────────────────  ◄ section_title

  3.  Prove that √2 is irrational.                            ← manual (symbolic)
      ☐  I solved this correctly (self-marked)                ← checkbox, marks[item.id]

  4.  Factor  x² − 5x + 6  completely.                        ← manual
      ☑  I solved this correctly (self-marked)

  ┌─────────────────────────────────────┐
  │        Submit diagnostic           │                      ← "Submitting…" while pending
  └─────────────────────────────────────┘
  [ ⚠ Could not submit. Please try again. ]                   ← role=alert on error
```

- **[NEW] section headers:** the data has `section_title` per item; the current build does not
  render it. Group items under their `section_title` (e.g. *Fundamentals* vs *Problem
  solving*) — the AoPS instruments use these sections and they map to the `fund`/`ps` grading
  groups, so the grouping is meaningful, not cosmetic.
- **No timer** by default (placement diagnostics are not strictly timed in the prototype),
  though `elapsed_sec` is captured silently from mount. If a soft timer is wanted, surface it
  as a quiet stopwatch, not a countdown — see [Q4](#8-open-ux-questions).
- **Self-mark honesty:** keep the manual-item copy plain and non-judgmental — **"I solved this
  correctly (self-marked)."** The verdict is recomputed server-side from marks + auto answers.

**States**

| State | Copy / behavior |
|-------|-----------------|
| Loading | `Spinner` — **"Loading diagnostic…"** |
| Load error / 404 | `ErrorState` — **"Could not load this diagnostic"** |
| Filling | The form above; Submit always enabled (blanks allowed — they count as wrong/unmarked). |
| Submitting | Button → `Submitting…`, disabled. |
| Submit error | `ErrorState` — **"Could not submit. Please try again."** (answers retained). |
| Result | Replaced by [4.3 Diagnostic result](#43-diagnostic-result-verdict). |

**Mobile:** already single-column and stacks naturally; ensure text inputs are full-width and
checkboxes have a large (44px+) tap target with the label as part of the hit area.

### 4.3 Diagnostic result (verdict)

Renders `DiagnosticResultResponse`: `verdict` (`win | mid | low`), `passed`, `correct`/`total`,
`summary` (the recommendation line), and optionally `group_scores` + per-item `review[]`
(`DiagnosticItemReview`: `item_id`, `correct`, `manual`, `answer`). Current build shows only
verdict + summary + correct/total; the wireframe below is the **[NEW]** fuller version.

```text
  Introduction to Algebra B — result                                       ← h1, aria-live

  ┌────────────────────────────────────────────────────────────────────────────┐
  │  WIN                                                                         │  ← verdict, prominent
  │  You're ready for Introduction to Algebra B. Strong on problem solving;      │  ← summary (from API)
  │  brush up fundamentals before you start.                                    │
  │                                                                             │
  │  9 of 12 correct.   Passed.                                                 │  ← correct/total + passed
  └────────────────────────────────────────────────────────────────────────────┘

  Section scores                                              ← [NEW] from group_scores (if present)
  ┌──────────────────┬─────────┐
  │  Fundamentals    │   4     │
  │  Problem solving │   5     │
  └──────────────────┴─────────┘

  Per-item review                                             ← [NEW] from review[] (optional, collapsible)
  ┌─────┬────────────┬───────────────────────┐
  │ Item│  Outcome   │  Answer               │
  ├─────┼────────────┼───────────────────────┤
  │  1  │  Correct   │  17                   │
  │  2  │  Incorrect │  3/2                  │
  │  3  │  Self ✓    │  (self-marked)        │   manual=true → outcome from the student's mark
  │  …  │            │                       │
  └─────┴────────────┴───────────────────────┘

  [ Back to diagnostics ]        [ View my progress ]         ← [NEW] next steps
```

- **Verdict treatment:** map `win/mid/low` to calm, legible emphasis — a labeled badge with
  text (**Ready / Almost / Not yet** as friendly synonyms, or keep the raw `WIN/MID/LOW` the
  code currently uppercases). Reinforce with text, never color alone.
- **Per-item review** is the only place a diagnostic `answer` is revealed (mirrors the exam
  key rule). Manual items show the student's self-mark, not a key.
- The summary line is authoritative recommendation copy from the server — render it verbatim;
  do not paraphrase.
- On success the progress query is invalidated, so `/progress` reflects this attempt.

---

## 5. Progress & recommendation

### 5.1 My progress dashboard (`/progress`)

`GET /api/v1/progress` → `ProgressResponse`. The shared `ProgressView` renders three blocks:
**Recommendation** (`recommendation_course`, `recommendation_reason`, `algebra_warning`,
`unlocked_by_amc[]`), **Contest history** (`test_attempts[]`), and **Diagnostics**
(`diagnostic_attempts[]`). Matches `ProgressPage.tsx` + `ProgressView.tsx`.

```text
  Your progress                                                            ← h1

  ┌── Recommendation ──────────────────────────────────────────────────────────┐
  │                                                                             │
  │  Introduction to Algebra B                       ← recommendation_course (h2 region) │
  │                                                                             │
  │  Your diagnostics place you mid-ladder; your AMC 10 score clears the gate   │  ← recommendation_reason
  │  for Algebra B, so start there.                                             │
  │                                                                             │
  │  ⚠ Your algebra fundamentals look shaky — review them before the first      │  ← algebra_warning
  │     class.                                                                  │     (role="alert", only if present)
  │                                                                             │
  │  Your AMC score unlocks: Algebra B, Counting & Probability.                 │  ← unlocked_by_amc (if any)
  └─────────────────────────────────────────────────────────────────────────────┘

  ┌── Contest history ─────────────────────────────────────────────────────────┐
  │  Score        │ Correct │ Wrong │ Blank │ Time (s)                          │
  │  105 / 150    │   17    │   6   │   2   │  4120                             │
  │  96 / 150     │   15    │   8   │   2   │  4500                             │
  └─────────────────────────────────────────────────────────────────────────────┘

  ┌── Diagnostics ─────────────────────────────────────────────────────────────┐
  │  Instrument        │  Verdict │  Result                                     │
  │  algB-pre          │   win    │  Passed                                     │
  │  pa1-pre           │   mid    │  Did not pass                               │
  └─────────────────────────────────────────────────────────────────────────────┘
```

- **Recommendation block first** — it is the headline output of the whole app. The
  `recommendation_reason` is server-authored; render verbatim.
- `algebra_warning` renders as a `role="alert"` only when non-null (the prototype's algebra
  gate). `unlocked_by_amc` renders as a sentence only when the array is non-empty.
- **[NEW]** Contest-history rows should identify **which paper** (e.g. *AMC 10 2022A*) and
  **when**; the current `ProgressResponse.test_attempts` items are untyped (`items: {}` in the
  schema) and the table keys off `score/correct/wrong/blank/time_used_sec`. If the attempt
  objects carry an exam label/date, surface them as the first column; if not, flag the API gap
  ([Q5]). Same for diagnostics (`instrument_id` is shown raw — prefer the human `course —
  kind` if available).

**States**

| State | Copy / behavior |
|-------|-----------------|
| Loading | `Spinner` — **"Loading progress…"** |
| Error | `ErrorState` — **"Could not load your progress"** |
| No recommendation yet | `EmptyState` in the recommendation block — **"No recommendation yet."** (plus the `recommendation_reason`, which may explain what's missing, e.g. "Take a diagnostic to get a placement.") |
| No contests | `EmptyState` — **"No contests taken yet."** |
| No diagnostics | `EmptyState` — **"No diagnostics taken yet."** |
| Fresh account (all empty) | All three empties stack; consider a single calming lead-in: **"Take a practice test or a diagnostic to get started."** with links to `/exams` and `/diagnostics`. **[NEW]** |

**Mobile:** the three blocks stack (already vertical). The two history **tables** are the only
wide elements — apply the same treatment as the review table: horizontal scroll within the
card, or collapse each attempt into a stacked mini-card (`AMC 10 2022A · 105/150 · 17✓ 6✗ 2—
· 4120s`). Keep the Recommendation block full-width and untruncated.

### 5.2 Coach's view of a student (`/users/:userId/progress`)

Staff-only. Same `ProgressResponse` and the **same `ProgressView`** as 5.1, so the layout is
identical — only the framing differs (h1 = **"Student progress"**, read-only). Matches
`UserProgressPage.tsx`.

```text
  Student progress                                                         ← h1
  ┌──────────────────────────────────────────────────────────────────────┐
  │  [ ← Back to students ]   Bayden  ·  bayden@example.com   ·  student   │  ← [NEW] context bar
  └──────────────────────────────────────────────────────────────────────┘

  …identical Recommendation / Contest history / Diagnostics blocks as §5.1…
  (read-only; no controls that mutate the student's data)
```

- **[NEW] student context bar:** the coach needs to know *whose* progress this is. The current
  page shows a generic "Student progress" heading with no name. Add a context bar with the
  student's `display_name` / `email` / `role` and a **"Back to students"** link. (Requires
  either a roster endpoint or fetching the target user — see [Q7].)
- Everything is **read-only**: a coach observes, never edits a student's attempts.

**States** mirror 5.1, plus:

| State | Copy / behavior |
|-------|-----------------|
| Loading | `Spinner` — **"Loading progress…"** |
| Error / 403 (non-staff) | Guard redirects non-staff home before render; a server 403 → `ErrorState` **"You don't have access to this student."** |
| 404 (no such user) | `ErrorState` — **"Could not load this student's progress"** (matches current copy). |

### 5.3 Coach roster — the missing entry point [NEW]

There is currently **no UI path** from the coach's nav to `/users/:id/progress`; the route
exists but is unreachable without typing a UUID. This is an IA gap. Proposed minimal solution
(pending a list-students endpoint — [Q7]):

```text
  Students                                                                 ← [NEW] page, staff-only
  ┌──────────────────────────────────────────────────────────────────────┐
  │  Bayden        bayden@example.com    last active 2d ago        →      │
  │  Avery         avery@example.com     last active 5d ago        →      │
  │  …                                                                    │
  └──────────────────────────────────────────────────────────────────────┘
       ↑ each row → /users/:id/progress
```

- Add a **"Students"** nav item (staff-only, next to "Invite"), or fold the roster into a
  staff landing page. Route suggestion: `/students` (not yet in the router).
- Until a roster endpoint exists, a coach reaches a student only via a link the app generates
  elsewhere (e.g. from the invite flow once the account is created). Flagged as [Q7].

---

## 6. Invite (staff-only) — `/invite`

Mint a one-time invite via `POST /api/v1/invites` (`InviteCreateRequest`: `email`, `role`).
The response (`InviteCreatedResponse`: `token`, `email`, `role`) returns the raw `token`
**exactly once**; the page builds the shareable link `…/register?token=<token>`. Matches
`InvitePage.tsx`.

```text
  Invite a student                                                         ← h1

  Email
  ┌─────────────────────────────────────┐
  │ avery@example.com                   │
  └─────────────────────────────────────┘

  Role
  ┌─────────────────────────────────────┐
  │ student            ▾                │   ← select: student / coach / admin
  └─────────────────────────────────────┘

  ┌─────────────────────────────────────┐
  │          Create invite             │   ← "Creating…" while pending
  └─────────────────────────────────────┘
  [ ⚠ Could not create the invite. ]       ← role=alert on error

  ── after success ───────────────────────────────────────────────────────────

  ┌── Share this link once ────────────────────────────────────────────────────┐
  │  Send this to avery@example.com. It won't be shown again.                   │
  │                                                                             │
  │  https://amc.example.com/register?token=R7xK…q1                ⧉ Copy       │  ← code + [NEW] copy button
  └─────────────────────────────────────────────────────────────────────────────┘
```

- **One-time disclosure is the key UX risk.** The raw token is shown once and never again.
  Make this unmissable: heading **"Share this link once"**, helper **"It won't be shown
  again."**, and **[NEW]** a **Copy** button (the current build shows the link in a `<code>`
  block with no copy affordance — easy to lose). After copying, confirm with **"Copied."**
- **[NEW] post-create affordances:** offer **"Create another invite"** (resets the form) and,
  once the invitee registers, a path to their progress (ties into the roster, [Q7]).
- Role select defaults to **student**; coaches will rarely mint coach/admin — consider hiding
  `admin` for non-admins, or confirming on elevated roles. ([Q9])

**States**

| State | Copy / behavior |
|-------|-----------------|
| Default | Empty email, role=student, Create enabled. |
| Submitting | Button → `Creating…`, disabled. |
| Error | `ErrorState` — **"Could not create the invite."** (e.g. invalid role, or non-staff 403). |
| Success | The "Share this link once" panel (`aria-live="polite"`) with the link + Copy. |

---

## 7. Core user journeys (end to end)

### US-001 — Take a timed AMC test → graded review

```text
[Login] ──► /exams ──► pick "AMC 10 2022A" ──► /exams/:id (RUNNER, key-free)
                                                   │
            ┌──── answer A–E · flag · navigate via palette · timer counts down ───┐
            │                                                                     │
            ▼                                                                     ▼
   manual Submit ──► [Confirm if blanks] ──► POST /exams/:id/attempts      timer hits 0
                                                   │                        ──► "Time's up —
                                                   │   (same guarded submit)    submitting…"
                                                   ▼                              │
                                          ExamResultResponse  ◄────────────────────┘
                                                   │
                                                   ▼
                                  /exams/:id (REVIEW — key revealed: score + per-problem)
                                                   │
                                   [Back to tests]  ·  [View my progress]
```

Acceptance hooks: timer counts down from `duration_sec` and auto-submits at zero; flag +
palette navigation work; on submit the server grades and stores; review shows correct answers.
The key is revealed only in the review (the runner never holds it).

### US-002 — Redeem invite → register → first login

```text
Coach: /invite ──► POST /invites ──► copies  …/register?token=XYZ  ──► sends to student
                                                                          │
Student: opens link ──► /register?token=XYZ                               ▼
            │  GET /auth/invites/{token}  (valid?  show email : show "invalid/expired")
            ▼
   enter display name + password (8+) ──► POST /auth/register ──► server sets amc_session cookie
            │
            ▼
   /auth/me re-derives user ──► redirect to / ──► /exams   (first login lands in the catalog)

Returning later: /login ──► email + password ──► POST /auth/login ──► cookie ──► /exams
```

Acceptance hooks: coach mints an invite; student sets a password and logs in; session persists
via the secure cookie; `/auth/me` returns the user; history follows the account across devices.

### US-003 — Take diagnostics → see placement recommendation

```text
/diagnostics ──► pick "Algebra B — Are You Ready?" ──► /diagnostics/:id (RUNNER)
        │
        │   auto items: type answer        manual items: work on paper, ☑ self-mark
        ▼
   Submit diagnostic ──► POST /diagnostics/:id/attempts  {responses, marks, elapsed_sec}
        │
        ▼
   DiagnosticResultResponse  (verdict win/mid/low · summary · correct/total · group_scores)
        │
        ├──► [Back to diagnostics]  (take more instruments)
        └──► /progress  ──► combined read: recommendation_course + reason
                              (+ algebra_warning, unlocked_by_amc from the AMC gate)
```

Acceptance hooks: the recommendation reflects the latest attempts and matches the prototype's
ladder + AMC-gate logic. Diagnostics feed `/progress`, where the AMC score and diagnostics are
synthesized into one `recommendation_course` + `recommendation_reason`.

### Coach journey — mint an invite, view a student's progress

```text
/invite ──► create invite ──► "Share this link once" (copy)  ──► [later] student registers
   │
   ▼
[Students roster — NEW]  ──► pick "Bayden"  ──► /users/:id/progress
                                                     │
                                                     ▼
                              read-only ProgressView: recommendation + contest + diagnostics
                                          [ ← Back to students ]
```

Acceptance hooks: a coach can open any student's progress; a student cannot open another's
(403). **Gap:** the roster step is [NEW] — the route exists but the entry point does not (see
[5.3](#53-coach-roster--the-missing-entry-point-new) and [Q7]).

---

## 8. Open UX questions

Decisions to confirm with the team. Each notes a recommended default so engineering is not
blocked.

| # | Question | Recommendation |
|---|----------|----------------|
| **Q1** | **Confirm before a manual submit?** The current runner submits with no confirmation. | **Confirm only when blanks (or flags) remain**; skip the dialog if every problem is answered. Auto-submit at zero never confirms. |
| **Q2** | **Show a ticking clock or a countdown?** | **Countdown** of time *remaining* (`M:SS`), matching `useCountdown`/`formatDuration` already built. A countdown maps to the real constraint better than elapsed time. |
| **Q3** | **Warn at low time?** No warning exists today. | **Yes** — non-color emphasis + one-shot `aria-live` announcements at **5:00** and **1:00** remaining. |
| **Q4** | **Time the diagnostics?** `elapsed_sec` is captured but not shown. | **No visible timer** (placement, not a contest); keep silent capture. If wanted, a quiet stopwatch, never a countdown. |
| **Q5** | **What identifies a contest-history row?** `ProgressResponse.test_attempts` items are untyped; the table keys off score/correct/wrong/blank/time only. | Surface **exam label (AMC 10 2022A) + date** as the first column. Needs the attempt objects to carry an exam ref/timestamp — **API follow-up** if absent. |
| **Q6** | **Show solution links in the exam review?** `Problem.solution_url` exists in the data model but `ReviewItemResponse` does not expose it. | Add `solution_url` to the review item and render a per-row **"Solution"** link. **API follow-up.** |
| **Q7** | **How does a coach reach a student?** `/users/:id/progress` has no entry point. | Add a **staff-only "Students" roster** (`/students`) backed by a list-students endpoint; rows link in. **API + route follow-up.** Until then the route is unreachable in normal use. |
| **Q8** | **Surface login rate-limiting?** | Default to the generic error to avoid enumeration; only show a specific "too many attempts" message if the API returns a distinguishable signal. |
| **Q9** | **Restrict which roles a coach can mint?** Invite role select currently lists student/coach/admin to all staff. | Default role **student**; hide/disable **admin** for non-admins, or confirm on elevated roles. |
| **Q10** | **Reconnect / resume an in-progress exam?** State is in-memory; a refresh restarts the runner and the in-memory timer. | Out of scope for v1 (single-sitting). Flag the data-loss risk: a mid-exam refresh loses unsaved answers. Consider a "leave page?" `beforeunload` guard while `phase==='active'`. |
| **Q11** | **Empty-state guidance for a brand-new account?** | Add a one-line lead-in on `/progress` linking to `/exams` and `/diagnostics` (see [5.1](#51-my-progress-dashboard-progress)). |

---

## 9. Cross-cutting UX standards

- **Status is never color-only.** Every status (palette cell, outcome, verdict, warning) pairs
  color with text and/or a glyph + ARIA, per the convention in `States.tsx`, `Palette.tsx`,
  and `ExamReview.tsx`. This is both an accessibility requirement and a fit with the
  clean-academic tone.
- **One canonical loading / empty / error vocabulary** via the shared `Spinner` / `EmptyState`
  / `ErrorState` components — reuse them everywhere rather than bespoke states. Loading copy is
  always context-specific ("Loading tests…", "Loading exam…", "Loading progress…").
- **Server copy is authoritative.** `recommendation_reason`, diagnostic `summary`, and
  `algebra_warning` are rendered verbatim; the UI frames them but does not rewrite them.
- **Calm, exam-serious microcopy.** Short, declarative, no exclamation marks except the genuine
  urgency of "Time's up". No celebratory or gamified language — this is a study aid for a coach
  and serious students.
- **Focus & keyboard.** The palette grid, radiogroups, and dialogs are keyboard-navigable;
  focus is visible (`focus-ring` token) and moves into/out of the confirm dialog correctly. The
  runner must be fully operable without a mouse (palette jump, A–E selection, flag, submit).
- **Responsive intent.** Desktop is the primary surface (a focused, exam-like single view);
  mobile is a supported stacked variant. The two complex screens — the **runner** and the
  **progress dashboard** — have explicit stacked layouts above; everything else stacks
  naturally in a single column.

---

## Appendix A — Screen ⇄ API ⇄ source map

| Screen | Route | API (method path) | Key response fields | Existing source |
|--------|-------|--------------------|---------------------|-----------------|
| Login | `/login` | POST `/auth/login`; GET `/auth/me` | `UserResponse{id,email,display_name,role}` | `pages/LoginPage.tsx` |
| Register | `/register?token=` | GET `/auth/invites/{token}`; POST `/auth/register` | `InviteValidationResponse{valid,email,role}` | `pages/RegisterPage.tsx` |
| Exam list | `/exams` | GET `/exams?contest=` | `ExamSummary[]` | `pages/ExamListPage.tsx` |
| Exam runner | `/exams/:id` | GET `/exams/{id}` | `ExamDetail{…,problems:ProblemRead[]}` (no key) | `pages/ExamRunnerPage.tsx`, `features/exam/*` |
| Exam review | `/exams/:id` (post-submit) | POST `/exams/{id}/attempts` | `ExamResultResponse{score,max_score,correct,wrong,blank,review[{n,your,correct,ok,voided}]}` | `features/exam/ExamReview.tsx` |
| Diagnostic list | `/diagnostics` | GET `/diagnostics` | `DiagnosticSummary[]` | `pages/DiagnosticListPage.tsx` |
| Diagnostic runner | `/diagnostics/:id` | GET `/diagnostics/{id}` | `DiagnosticDetail{instructions,items:DiagnosticItemRead[{…,manual}]}` (no key) | `pages/DiagnosticRunnerPage.tsx` |
| Diagnostic result | `/diagnostics/:id` (post-submit) | POST `/diagnostics/{id}/attempts` | `DiagnosticResultResponse{verdict,passed,correct,total,summary,group_scores,review[]}` | `pages/DiagnosticRunnerPage.tsx` |
| My progress | `/progress` | GET `/progress` | `ProgressResponse{test_attempts[],diagnostic_attempts[],recommendation_course,recommendation_reason,unlocked_by_amc[],algebra_warning}` | `pages/ProgressPage.tsx`, `features/progress/ProgressView.tsx` |
| Student progress | `/users/:id/progress` | GET `/users/{id}/progress` | `ProgressResponse` (same) | `pages/UserProgressPage.tsx`, `features/progress/ProgressView.tsx` |
| Invite | `/invite` | POST `/invites` | `InviteCreatedResponse{token,email,role}` (token once) | `pages/InvitePage.tsx` |
| Students roster | `/students` **[NEW]** | *list-students endpoint TBD* ([Q7]) | TBD | *not yet built* |

---

## Related documents

- [Project Vision](../planning/project-vision.md)
- [Technical Spec](../planning/tech-spec.md)
- [Roadmap](../planning/roadmap.md) — US-001 / US-002 / US-003
- [OpenAPI schema](../api/openapi.json) — response shapes designed around
