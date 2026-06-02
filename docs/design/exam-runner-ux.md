---
title: "AMC Trainer - Timed Exam Runner UX Specification"
schema_type: common
status: draft
owner: core-maintainer
purpose: "Definitive, implementation-ready UX spec for the timed exam runner."
tags:
  - design
  - user_experience
  - accessibility
  - frontend
  - specifications
---

> **Status**: Draft | **Updated**: 2026-05-31 | **Scope**: US-001, the timed exam runner

## How to read this spec

This is a **deep-dive UX spec that refines a working implementation**, not a greenfield
proposal. The runner already exists and works. Throughout, status callouts mark the
relationship between this spec and the code:

- **[MATCHES]** - the current code already does this; the spec documents and pins the behavior.
- **[EXTENDS]** - a concrete addition or change layered on top of what exists today.
- **[RISK]** - a current behavior that is a UX hazard; the spec recommends a stance.

Real symbol names are used so this reads against the source. The reducer
(`runnerReducer`, `RunnerState`, `RunnerPhase`, `RunnerAction`) in
`frontend/src/features/exam/runnerState.ts`, the timer (`useCountdown`,
`formatDuration`) in `useCountdown.ts`, and the components `Palette`, `Question`,
`ExamReview`, `Tex`, plus the page `ExamRunnerPage` (`RunnerInner`) are the things being
specced. API shapes (`ExamDetail`, `ProblemRead`, `ExamSubmission`, `ExamResultResponse`,
`ReviewItemResponse`) come from `docs/api/openapi.json`.

> **Note on styling source of truth.** The project brief describes "CSS Modules + design
> tokens". The current implementation uses a **single global stylesheet**
> `frontend/src/index.css` with design tokens in `:root` and BEM-ish class names
> (`.runner__timer`, `.palette__cell--answered`, …). This spec references the **real**
> tokens (`--color-primary: #2d4ea2`, `--color-warn: #9a5b00`, `--color-error: #b00020`,
> `--color-ok: #1b7f4b`, `--space-*`, `--radius`, `--maxw: 960px`). Where it says "add a
> class", that means add to `index.css` (or a future co-located module) - the naming and
> token usage are what matter, not the file boundary.

---

## 1. Goals & Constraints

The exam runner is the product's centerpiece. A timed test is an inherently high-stress,
low-tolerance-for-ambiguity surface: a student under a ticking clock has no spare attention
for a confusing UI, and a lost answer or a surprise auto-submit is a trust-destroying event.
Every decision below serves five non-negotiable goals.

### 1.1 The five goals

1. **Reduce anxiety.** The default visual state is calm and academic (the project's tone).
   The clock does not shout until it must. Nothing flashes, pulses, or turns red without a
   real reason. The student should feel they are sitting a paper, not playing a game-show.

2. **Zero ambiguity about state.** At every moment the student can answer, without thinking:
   *How much time is left? Which question am I on? Which have I answered? Which did I flag?
   What happens if I press Submit?* The palette (`Palette.tsx`) and the header progress line
   carry most of this load; the spec tightens them so state is never inferred, always shown.

3. **Never lose work.** Answers and flags live in the reducer
   (`RunnerState.answers`, `RunnerState.flags`) and are only ever read, never silently
   dropped, until submission. The largest residual risk here is **page refresh mid-exam**,
   which today discards everything (see §7.1) - this spec flags it as the top correctness
   issue and recommends persistence.

4. **The timer is sacred.** The clock is an **absolute deadline**, computed from
   `startedAt + durationSec` (`useCountdown`), not a decrementing counter. It does not drift,
   does not pause when the tab is backgrounded, and **auto-submits exactly once** at zero.
   The UI must never present the timer as something that can be paused, gamed, or "stopped"
   by leaving the page. **[MATCHES]** - this is the existing `useCountdown` contract, and the
   spec's job is to make the *visible* timer faithful to it.

5. **Integrity: no answer key before submission.** `ExamDetail` / `ProblemRead` deliberately
   carry **no `correct_answer` field** (the schema description says so explicitly). The
   review screen (`ExamReview`, rendering `ExamResultResponse.review`) is the **only** place
   a correct answer ever appears. Nothing in the active runner - not a tooltip, not a hint,
   not a "check answer" affordance - may reveal or imply correctness. This is a hard
   acceptance criterion from the roadmap ("No `correct_answer` in any pre-submission API
   response or page source").

### 1.2 Constraints inherited from the architecture

| Constraint | Source | UX consequence |
|---|---|---|
| Grading is server-side only | tech-spec; `submitExam` → `ExamResultResponse` | The client cannot show a score or mark a question correct until the POST returns. No optimistic scoring. |
| Single submission per attempt; 409 on repeat | `RunnerInner` `onError` handles `status === 409` | Submit must be guarded against double-fire (timer + button); a 409 is treated as "already submitted, show result". |
| Absolute-deadline timer, fires once | `useCountdown` (`firedRef` guard) | Auto-submit is unconditional at zero; the visible timer must not lie about remaining time. |
| Two render modes per problem | `ProblemRead.render_mode` ∈ `latex` \| `image` | The question area must handle both KaTeX bodies and scanned-image papers (AMC 10 scans). |
| Two score modes | `score_mode` ∈ `sixpoint` \| `count` | Review framing differs (6-point vs. raw count); blank ≠ wrong for `sixpoint`. |
| Voided problems exist | `ExamDetail.voided` (1-based numbers) | Voided problems must be visibly distinct in palette and review and excluded from scoring. |
| Same-origin SPA, session cookie | ADR-002 | Submit is a normal authenticated POST; auth errors (401) are possible and must be handled (see §7.2). |

### 1.3 Out of scope (so the runner stays focused)

Per the roadmap, the runner is US-001 only. **Not** in scope here: catalog/selection,
login/onboarding (US-002), diagnostics (US-003), the progress dashboard, or coach views.
The runner *invalidates* the progress query on submit
(`queryClient.invalidateQueries({ queryKey: queryKeys.progress() })`) but does not render it.

---

## 2. Layout & Anatomy

The runner is one route (`ExamRunnerPage` → `RunnerInner`) with three phases driven by
`RunnerPhase` (`active` → `submitting` → `review`). The **active** layout has three regions:
a **header**, a **palette/navigator**, and a **question column** (body + controls). The
container is capped at `--maxw` (960px) and centered.

### 2.1 Desktop - active phase (≥ 720px)

The current grid is `grid-template-columns: 12rem 1fr` at the `min-width: 720px`
breakpoint (`.runner__body`), palette on the left, question on the right.

```
┌───────────────────────────────────────────────────────────────────────────┐
│  HEADER  (.runner__header - flex, wrap, baseline-aligned)                    │
│                                                                             │
│  AMC 10 2023 A                         ⏱ 1:04:18           14 of 25 answered │
│  (contest year variant, <h1>)          (.runner__timer,    (.runner__progress│
│                                         role="timer")       aria-live polite)│
├──────────────┬──────────────────────────────────────────────────────────────┤
│  PALETTE     │  QUESTION COLUMN  (.runner__question)                         │
│ (.palette,   │                                                               │
│  <nav>)      │   Problem 12               (.question__number, <h2>)          │
│              │                                                               │
│  ┌─┬─┬─┬─┬─┐ │   ┌───────────────────────────────────────────────────────┐  │
│  │1│2│3│4│5│ │   │  Let x be a real number such that … (KaTeX display)    │  │
│  ├─┼─┼─┼─┼─┤ │   │  or  [ scanned problem image, render_mode="image" ]    │  │
│  │6│7│8│9│⑩│ │   └───────────────────────────────────────────────────────┘  │
│  ├─┼─┼─┼─┼─┤ │                                                               │
│  │⑪│▣│13│14│15│  CHOICES (.choices, role="radiogroup")                       │
│  ├─┼─┼─┼─┼─┤ │   ( ) A   2/5                                                 │
│  │…│…│…│…│25│ │   (•) B   3/5     ← selected                                 │
│  └─┴─┴─┴─┴─┘ │   ( ) C   4/5                                                 │
│              │   ( ) D   1                                                    │
│  legend ↓    │   ( ) E   6/5                                                 │
│  ▣ flagged   │                                                               │
│  ⑩ current   │   [ Clear answer ]   (.link-button, only when an answer set)  │
│  ░ voided    │                                                               │
│  █ answered  │   CONTROLS (.runner__controls)                                │
│              │   [ Previous ] [ Flag ] [ Next ]            [   Submit   ]     │
│              │    disabled at 0  toggles  disabled at end   (.runner__submit, │
│              │                                               right-aligned)   │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

**Header anatomy** (`.runner__header`, flex / wrap / `align-items: baseline`):

- **Contest title** - `<h1>` rendering `{exam.contest} {exam.year}{exam.variant}`
  (e.g. "AMC 10 2023 A"). Left-aligned, the page's main heading.
- **The timer** - `.runner__timer`, `role="timer"`, the visual anchor of the whole screen
  (see §3). `font-variant-numeric: tabular-nums` so digits don't jiggle as they tick.
- **Answered-count progress** - `.runner__progress`, "{answeredCount(state)} of
  {state.numProblems} answered", `aria-live="polite"`. This is the at-a-glance "how far am
  I" readout. **[EXTENDS]** add a slim, non-color progress affordance (a thin underline bar
  whose width = answered/total) so progress is perceivable pre-attention, not only on read.

**Question area** (`.runner__question`): problem number `<h2>` ("Problem {number}"), then
the **body** (`.question__body` - KaTeX `display` via `<Tex>` or `<img>` scan), then the
A–E **radiogroup** (`.choices`), then a conditional **Clear answer** link-button.

**Controls** (`.runner__controls`): Previous / Flag / Next / Submit. Submit is visually
primary (`--color-primary` fill) and pushed to the right with `margin-left: auto`.

### 2.2 Mobile - active phase (< 720px)

At narrow widths the grid collapses to a single column (`grid-template-columns: 1fr`), and
today the palette simply stacks **above** the question. That is workable but pushes the
question below the fold and wastes vertical space on a 25-cell grid. **[EXTENDS]** convert
the palette into a **drawer/sheet** so the question is the hero and the navigator is one tap
away.

```
┌─────────────────────────────────┐    Tapping "Questions ▾" or the
│ AMC 10 2023 A                   │    progress chip opens the sheet:
│ ⏱ 1:04:18      14/25 answered   │
├─────────────────────────────────┤    ┌─────────────────────────────┐
│ [ ☰ Questions ▾ ]   (sticky)    │    │  Question navigator      [✕]│
├─────────────────────────────────┤    │  ┌─┬─┬─┬─┬─┐                │
│ Problem 12                      │    │  │1│2│3│4│5│  █ answered     │
│                                 │    │  ├─┼─┼─┼─┼─┤  ▣ flagged      │
│  (KaTeX body / image scan)      │    │  │6│7│8│9│⑩│  ⑩ current     │
│                                 │    │  ├─┼─┼─┼─┼─┤  ░ voided       │
│  ( ) A   2/5                    │    │  │⑪│▣│…│…│15│                │
│  (•) B   3/5                    │    │  └─┴─┴─┴─┴─┘                │
│  ( ) C   4/5                    │    │  (tap a cell → jumps,       │
│  ( ) D   1                      │    │   sheet closes)             │
│  ( ) E   6/5                    │    └─────────────────────────────┘
│  [ Clear answer ]               │
├─────────────────────────────────┤    The header (timer) stays fixed/
│ STICKY FOOTER BAR               │    sticky at the top so the clock is
│ [‹ Prev] [⚑ Flag] [Next ›]      │    always visible while scrolling a
│           [   Submit   ]        │    long problem.
└─────────────────────────────────┘
```

Mobile specifics:

- **Header is sticky** (`position: sticky; top: 0`) so the **timer is always visible** while
  scrolling a long problem - on mobile the clock must never scroll away.
- **Controls become a sticky bottom bar** so Prev/Flag/Next/Submit are reachable without
  scrolling to the end of a tall question. Submit retains primary styling but, on mobile,
  Prev/Next get larger 44×44px minimum hit targets.
- **Palette → sheet**: a labeled trigger ("Questions") that announces flagged/unanswered
  counts; the sheet is a `role="dialog"` with a focus trap and `Esc`/backdrop to close.
  Selecting a cell dispatches `goto` and closes the sheet, returning focus to the question.

### 2.3 Phase layouts (submitting / review)

- **`submitting`** - the active layout stays mounted but **frozen** (`frozen = state.phase
  !== 'active'`): radiogroup `disabled`, Flag/Submit disabled, Submit label reads
  "Submitting…". **[EXTENDS]** overlay a calm, non-blocking "Submitting your answers…"
  status with a spinner so the freeze is explained, not mysterious.
- **`review`** - `RunnerInner` returns `<ExamReview result={result} />`, a full-width page
  (no palette, no timer). See §6.

---

## 3. The Timer

The timer is the single most important pixel on the screen. It is also the easiest thing to
get wrong - a timer that drifts, pauses, or surprises the student destroys trust. The
behavioral contract is already correct in `useCountdown`; this section specs the **visual
and announcement** layer on top of it.

### 3.1 Behavioral contract (pinned to `useCountdown`) - [MATCHES]

- **Absolute deadline.** `deadline = startedAtMs + durationSec * 1000`. Every tick recomputes
  `remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000))`. **[RISK note]** the
  deadline anchors on `startedAtRef = Date.now()` at mount (client clock), not a server-issued
  `started_at`; see §7.1 for the refresh implication and recommendation.
- **No drift, no pause on backgrounding.** Because the value is derived from wall-clock time,
  a throttled background `setInterval` only makes updates *less frequent*, never *wrong*. When
  the tab refocuses, the displayed value snaps to the truth. The UI must **not** imply the
  clock can be paused.
- **Fires exactly once.** The `firedRef` guard ensures `onExpire` (→ `triggerSubmit`) runs a
  single time at zero. Combined with the reducer's idempotent `startSubmit` and the page's
  `if (state.phase !== 'active') return` guard, auto-submit cannot double up with a manual
  submit.

### 3.2 Format - [MATCHES] `formatDuration`

`formatDuration(totalSeconds)` renders `M:SS` under an hour and `H:MM:SS` at/over an hour.
AMC durations make both real: AMC 8 (40 min) and AMC 10/12 (75 min) both start as
`H:MM:SS` and cross into `M:SS` at the hour mark. `tabular-nums` keeps width stable across
the transition so layout never shifts.

### 3.3 Placement & calm-by-default styling

- **Placement.** Top of the header, second item, baseline-aligned with the title. On mobile,
  inside the sticky header so it is always on screen.
- **Calm default.** Normal state uses `--color-fg` on the default background at 1.5rem / 700
  weight (current `.runner__timer`). No border, no icon chrome beyond an optional small clock
  glyph, no animation. It reads like a clock on a wall.

### 3.4 Escalating urgency - shape/text/ARIA, not color alone

Urgency is conveyed **redundantly** (icon/shape + text label + ARIA), never by color alone,
satisfying WCAG 1.4.1 (Use of Color). Three tiers, thresholds chosen to be meaningful for a
40–75 min paper:

| Tier | Threshold (`remaining`) | Visual treatment | Text/shape | ARIA / announce |
|---|---|---|---|---|
| **Normal** | `> 300` (more than 5:00) | `--color-fg`, plain | clock glyph `⏱`, no badge | label only; no live announce |
| **Caution** | `≤ 300` and `> 60` (5:00–1:01) | `--color-warn` (#9a5b00) text + a subtle outlined "pill" around the timer; a small "5 min" milestone marker | append "- 5 minutes left" at the threshold crossing | one polite announcement at the 5:00 crossing |
| **Warning** | `≤ 60` (final minute) | `--color-error` (#b00020) text, **bordered** timer chip (border, not just color), `font-weight: 800` | a `▲` warning glyph + visible "1 min" badge | one assertive announcement at 1:00; then polite at 30s/10s (see §3.5) |

Notes:

- The **shape change** (no chrome → outlined pill → bordered chip with glyph) makes the tier
  legible to color-blind users and in grayscale. The data attribute `data-urgency="normal" |
  "caution" | "warning"` on `.runner__timer` drives CSS so the logic lives in one place.
- **No flashing/pulsing by default.** Under `prefers-reduced-motion: no-preference` a single,
  gentle one-shot scale "tick" at the 1:00 crossing is allowed; under reduced-motion it is
  suppressed entirely (§8.5). Anxiety reduction beats spectacle.
- Compute the tier from `remaining` in `RunnerInner` (it already has `remaining` from
  `useCountdown`); pass it to the timer element. This is purely presentational - **it never
  changes the deadline or the fire-once behavior**.

### 3.5 The `aria-live` cadence (do NOT announce every second)

Today the timer is `aria-live="off"` (correct - a per-second live region would flood a screen
reader and make the page unusable). But silence all the way to zero is its own hazard: a
non-sighted student deserves the same "time is running out" cues a sighted one gets from the
red chip. **[EXTENDS]** introduce a **separate, visually-hidden polite live region** that
announces on a sparse, milestone schedule - the visible `role="timer"` stays `aria-live="off"`.

Proposed announcement schedule (fire each **once**, on the second it crosses the threshold):

| `remaining` crosses | Announcement | politeness |
|---|---|---|
| 600 (10:00) | "10 minutes remaining." | polite |
| 300 (5:00) | "5 minutes remaining." | polite |
| 120 (2:00) | "2 minutes remaining." | polite |
| 60 (1:00) | "1 minute remaining." | **assertive** |
| 30 | "30 seconds remaining." | assertive |
| 10 | "10 seconds remaining." | assertive |
| 0 | "Time is up. Submitting your answers." | assertive |

Implementation: keep a `useRef<Set<number>>` of already-announced milestones (mirrors the
`firedRef` pattern) so each fires exactly once even though `tick()` runs every second. This
gives parity with the visual urgency tiers without per-second chatter.

### 3.6 The auto-submit-at-zero moment (what the student sees)

When `remaining` hits 0, `useCountdown` calls `onExpire` → `triggerSubmit` once. The student
experience must be **unambiguous and non-punitive**:

1. The timer reads `0:00` and shows the warning treatment (red, bordered, `▲`).
2. The live region announces "Time is up. Submitting your answers." (assertive).
3. **No confirmation dialog** - time is up; asking "are you sure?" would be cruel and could
   race the deadline. The auto path goes straight to `submitting`.
4. The radiogroup and controls are already frozen; **[EXTENDS]** show the same "Submitting
   your answers…" overlay as the manual path so the transition is explained.
5. On success, `dispatch({ type: 'submitted' })` → review. The student lands on their graded
   result with no extra clicks. If the POST fails, see §7.2 (the auto path needs a safety net
   so a network blip at the buzzer doesn't strand the student with no result).

> **Distinction that matters:** manual submit *asks first* (§5.1); auto submit *never asks*.
> The two share the single `triggerSubmit` entry point but differ in whether a confirmation
> precedes the call.

---

## 4. Answering & Navigation

### 4.1 Selecting and clearing a choice - [MATCHES] `Question.tsx`

- The five choices are a real **`role="radiogroup"`** (`.choices` fieldset), one
  `<input type="radio">` per choice, `name="problem-{number}"`, `checked` bound to
  `selected === choice.letter`. Selecting dispatches
  `{ type: 'answer', index: state.current, choice }`.
- **Choice rendering.** In `latex` mode each choice's HTML is rendered through `<Tex>` after
  `stripDelimiters` removes wrapping `\( \)` / `$ $`. In `image` mode the choice body is
  omitted (the scan shows the options); only the **A–E letters** render, so the radiogroup is
  still fully usable on image papers. The letter (`.choice__letter`, bold) is always shown.
- **Clearing.** When an answer is set and not frozen, a **Clear answer** link-button
  (`.link-button`) dispatches `{ type: 'clearAnswer', index }`, returning the problem to blank
  (`answers[index] = null`). This matters because **blank ≠ wrong** in `sixpoint` scoring
  (blank earns 1.5; wrong earns 0), so the student needs a first-class way to *un-answer* a
  guess. **[EXTENDS]** the visual selected-state on the chosen `.choice` should be stronger
  than the OS radio dot - e.g. a left accent bar + `--color-surface` fill on the selected
  label - so the current answer is unmistakable at a glance.

### 4.2 Flagging - [MATCHES] reducer + controls

- The **Flag** control toggles `{ type: 'toggleFlag', index: state.current }`; the button
  carries `aria-pressed={state.flags[current]}` and swaps its label between "Flag" / "Unflag".
- Flags are advisory only: they never affect scoring and are submitted in
  `ExamSubmission.flags` for the record. In the palette, a flagged cell shows a `⚑` glyph and
  a warning-colored border (`.palette__cell--flagged`), so flagging is visible globally, not
  just on the current question.

### 4.3 Moving between questions - [MATCHES]

- **Prev / Next** dispatch `prev` / `next`; the reducer `clampIndex`-es so they're safe at the
  ends, and the buttons are `disabled` at index 0 and `numProblems - 1` respectively.
- **Palette jump** - clicking a `.palette__cell` dispatches `{ type: 'goto', index }`; the
  reducer clamps. The current cell shows `aria-current="true"` and a primary outline
  (`.palette__cell--current`).
- **Navigation is always free.** There is no forced linear order and no "you must answer to
  proceed" gate - a student can skip, flag, and return. This is correct for a real contest and
  must be preserved.
- **[EXTENDS]** after selecting a choice, do **not** auto-advance. On a timed math test the
  student often wants to re-read or change an answer; auto-advance is a classic source of
  "it jumped and I lost my place" complaints. Advancing stays an explicit Next / palette
  action.

### 4.4 Keyboard model (full spec) - [EXTENDS] (none of this exists yet)

There is **no keyboard shortcut layer today** beyond native radio/button behavior. For a
power surface like a timed test, keyboard fluency is a major speed and accessibility win.
Bindings below are chosen to avoid clobbering browser defaults and to be discoverable.

**Within the choices (native radiogroup - already works):**

| Key | Action |
|---|---|
| `↑` / `←` | Move selection to previous choice (native radio behavior) |
| `↓` / `→` | Move selection to next choice (native radio behavior) |
| `Space` | Select the focused choice |
| `Tab` | Move focus out of the radiogroup to the next control |

> Because `↑↓←→` are owned by the radiogroup when focus is inside it, **question navigation
> must not also use bare arrows** - that would conflict. Hence the letter/number bindings below.

**Global runner shortcuts (active phase, when focus is not in a text field):**

| Key | Action | Dispatch |
|---|---|---|
| `A` `B` `C` `D` `E` | Select that choice for the current problem | `{ type: 'answer', choice }` |
| `1`–`9`, then multi-digit entry | Jump to that problem number (type "1" "2" → problem 12, short debounce) | `{ type: 'goto', index: n-1 }` |
| `N` or `]` or `PageDown` | Next problem | `{ type: 'next' }` |
| `P` or `[` or `PageUp` | Previous problem | `{ type: 'prev' }` |
| `F` | Toggle flag on current problem | `{ type: 'toggleFlag', index }` |
| `Backspace` or `Delete` | Clear current answer | `{ type: 'clearAnswer', index }` |
| `?` | Open a keyboard-shortcuts help sheet | (UI only) |
| `Esc` | Close any open sheet/dialog (palette sheet, help, confirm) | (UI only) |

Rules:

- Shortcuts are **suppressed while a dialog/sheet is open** (the dialog owns the keyboard),
  and while focus is in an input/textarea (none today, but future-proof).
- Shortcuts are **disabled once `phase !== 'active'`** (frozen), mirroring the reducer's edit
  guard, so a stray keystroke during `submitting` does nothing.
- A small, dismissible "Press ? for keyboard shortcuts" hint on first load aids discovery.
- Letter keys for answering must use `event.key` case-insensitively and ignore when modifier
  keys (`Ctrl`/`Meta`/`Alt`) are held, so browser shortcuts (Ctrl+F, etc.) are untouched.

**Palette keyboard model - roving tabindex** (the palette is a `<nav>` of buttons today):

- The palette grid implements **roving tabindex**: exactly one cell has `tabindex="0"` (the
  current problem), the rest `tabindex="-1"`. Arrow keys move focus within the grid (`←/→`
  by one, `↑/↓` by a row of 5 - matching the `repeat(5, 1fr)` layout), `Home`/`End` to first/
  last, `Enter`/`Space` to jump (`goto`). This makes the navigator a single Tab stop instead
  of 25, which is essential for keyboard and screen-reader users on a 25-cell grid.

---

## 5. Submitting

Submission is the moment of highest stakes: it is irreversible, it freezes the attempt, and it
is the boundary where the answer key appears. The flow maps directly onto `RunnerPhase`
(`active` → `submitting` → `review`) and the single `triggerSubmit` entry point in
`RunnerInner`.

### 5.1 Manual submit - confirm first - [EXTENDS]

Today the **Submit** button calls `triggerSubmit` **immediately** with no confirmation. For a
timed test where Submit ends the attempt, this is a footgun - a misclick (or a hurried student
who meant to press Next) ends everything. **[EXTENDS]** add a **confirmation dialog** on the
*manual* path only.

The dialog summarizes the consequences using reducer-derived counts (cheap to compute):

- `unanswered = state.numProblems - answeredCount(state)`
- `flagged = state.flags.filter(Boolean).length`
- (voided is informational; voided problems can't be "answered" for score)

```
┌───────────────────────────────────────────────┐
│  Submit your exam?                        [✕]  │
│                                                │
│  You have answered 14 of 25 problems.          │
│  • 11 unanswered                               │
│  • 3 flagged for review                        │
│                                                │
│  Submitting is final - you can't change        │
│  answers afterward.                            │
│                                                │
│  Time remaining: 1:04:18                       │
│                                                │
│         [ Keep working ]   [ Submit now ]      │
└───────────────────────────────────────────────┘
```

- `role="dialog"`, `aria-modal="true"`, labelled by its heading, focus trapped; initial focus
  on **Keep working** (the safe default) so an accidental `Enter` does not submit.
- **Submit now** calls `triggerSubmit`; **Keep working** / `Esc` / backdrop dismisses and
  returns focus to the Submit button.
- When `unanswered > 0` the copy is slightly emphasized ("11 unanswered") so the student
  doesn't submit a half-finished paper by accident - but submitting is never *blocked*.
- This dialog exists **only** on the manual path. The auto-submit path (§3.6, §5.2) bypasses
  it entirely.

### 5.2 Auto-submit path - no confirmation - [MATCHES] mechanism

When the deadline passes, `useCountdown` → `onExpire` → `triggerSubmit` runs once. There is
**no dialog** (time is up; consent is moot). The reducer flips `active → submitting`, the
mutation posts, and on success `submitted → review`. This is the existing wiring; the spec
only adds the "Submitting…" overlay and the §7.2 failure safety net.

### 5.3 Guarding against double-submit - [MATCHES]

Three independent guards already make double-submit impossible; the spec pins all three:

1. **Page guard** - `triggerSubmit` returns early if `state.phase !== 'active'`.
2. **Reducer guard** - `startSubmit` is idempotent: it only transitions *out of* `active`
   once (`state.phase === 'active' ? … : state`).
3. **Disabled controls** - once `frozen`, the Submit button is `disabled` and its label is
   "Submitting…", so it can't be clicked again.

Together these mean the **timer firing and the button being pressed at nearly the same
instant** still results in exactly one POST. (Documented in `RunnerInner`'s header comment;
this spec elevates it to a tested invariant - see §9.)

### 5.3a The submit payload - [MATCHES] `ExamSubmission`

`submitExam(exam.id, { answers, flags, time_used_sec })`. `RunnerState.answers` /
`flags` are already the exact `ExamSubmission` shape (the reducer was built to avoid
translation), and `time_used_sec = round((Date.now() - startedAtRef.current) / 1000)`. No
mapping layer is needed; the spec preserves this 1:1 alignment.

### 5.4 Handling the server's "already submitted" (409) - [MATCHES] intent

The mutation's `onError` checks `error instanceof ApiError && error.status === 409` and, if so,
dispatches `submitted` - treating the conflict as "this attempt already exists". **[EXTENDS,
small]** today a 409 transitions to `review` but `result` may be `null`, and `RunnerInner`'s
review branch requires `result !== null` - so a 409 with no body would leave a frozen active
screen. The spec requires: on 409, **fetch/return the existing `ExamResultResponse`** (the
endpoint should return the prior result body on conflict, or the client refetches the attempt)
and only then show review. The user-facing message is calm: "This exam was already submitted:
here's your result," never an error.

> **Note for the API:** the submit endpoint currently documents only 200/422 in
> `openapi.json`. The 409 path is implemented client-side defensively; the server contract
> should be updated to **return the existing result on a repeat submission** so the review can
> render. Logged as template/API feedback, not changed here.

### 5.5 Phase mapping summary

```
        manual Submit ──► [confirm dialog] ──┐
                                             ├─► triggerSubmit() ─► dispatch(startSubmit)
   timer hits 0 ─► onExpire (once) ──────────┘        │  phase: active → submitting
                                                       ▼
                                          submitExam(...) POST
                                            │                 │
                                    onSuccess(graded)     onError
                                            │              ├─ 409 → treat as submitted
                                  setResult(graded)        └─ other → retry UX (§7.2)
                                  dispatch(submitted)
                                  phase: submitting → review
                                            ▼
                                  <ExamReview result=… />
```

---

## 6. The Review Screen

Review (`ExamReview.tsx`, fed `ExamResultResponse`) is the payoff and the **only** place the
answer key appears. It must feel like getting a graded paper back: clear headline, honest
breakdown, and a per-problem table you can actually scan.

### 6.1 Score breakdown - [MATCHES] with framing additions

Current `ExamReview` renders a `<dl class="review__score">`: **Score** (`score / max_score`),
**Correct**, **Wrong**, **Blank**. Keep all four. **[EXTENDS]** make the framing
score-mode-aware (the result doesn't carry `score_mode`, but the originating `ExamDetail`
does, so `RunnerInner` can pass it to `ExamReview`):

- **`sixpoint`** (AMC 10/12): a one-line note that **blanks score 1.5 each and wrong scores 0**,
  so the "Blank" stat reads as a deliberate strategy, not just "didn't finish". Show
  `score / max_score` with one decimal (scores like `103.5` are normal under this rule).
- **`count`** (AMC 8): `score / max_score` as whole numbers; the note simplifies to "1 point
  per correct answer".
- Headline emphasis on **Score / max**; Correct / Wrong / Blank are the supporting stats.
  Optionally surface a percentage and (later) percentile, but never invent data the server
  didn't send.

```
┌────────────────────────────────────────────────────────────────┐
│  Your result - AMC 10 2023 A                                    │
│                                                                  │
│   Score          Correct      Wrong       Blank                  │
│   103.5 / 138      16            5           4                    │
│   (.review__score dl/dt/dd)                                      │
│                                                                  │
│   Blanks score 1.5 each; wrong answers score 0. (sixpoint note)  │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 Per-problem table - [MATCHES] columns, [EXTENDS] scannability

Current `<table class="review__table">` maps `result.review` (each `ReviewItemResponse`):
**# (`item.n`)**, **Your answer (`item.your ?? '-'`)**, **Correct (`item.correct`)**,
**Outcome** (`outcome(item.voided, item.ok)` → "Void" / "Correct" / "Incorrect"). Keep these
columns; the field-by-field source of truth is:

| Column | Source field | Notes |
|---|---|---|
| `#` | `item.n` | 1-based problem number |
| Your answer | `item.your` | `null` → render `"-"` (a true blank) |
| Correct | `item.correct` | **The answer key - only appears here** |
| Outcome | `item.ok`, `item.voided` | voided wins: "Void"; else `ok` → "Correct"/"Incorrect" |

Making **25 rows scannable** (these papers are always 25 problems):

- **Outcome carries an icon + word**, not color alone: `✓ Correct` (`--color-ok`),
  `✗ Incorrect` (`--color-error`), `∅ Void` (muted). Redundant encoding = WCAG 1.4.1.
- **Quiet zebra striping** and a **sticky `<thead>`** so the header stays while scrolling 25
  rows.
- **Visually distinguish wrong-vs-blank**: a wrong answer (`your` set, `ok=false`) reads
  differently from a blank (`your` null) - the blank row shows `"-"` and a muted "Blank"
  sub-label on Outcome, because under `sixpoint` they have very different point values and the
  student's review intent differs ("I missed this" vs. "I skipped this").
- **Right-align** the short answer columns (single letters) and keep `#` narrow so the eye
  tracks rows quickly.
- **[EXTENDS] filter chips** - "All / Incorrect / Flagged / Blank" - let a student jump
  straight to what they got wrong on a 25-row table. (Flagged requires carrying the
  submission's `flags` into review, which `RunnerInner` already holds in `state.flags`.)
- **[EXTENDS] solution link out** - link each row to the AoPS Wiki solution. **This does not
  exist today**: `ReviewItemResponse` carries no per-problem URL, and `ExamResultResponse` no
  exam-level link. The server *does* store `Exam.source_url` (the AoPS Wiki page, per
  tech-spec) but it is **not exposed** in any response. Recommendation: add an optional
  per-problem `solution_url` (or at minimum surface the exam-level `source_url`) to
  `ReviewItemResponse` / `ExamResultResponse`, then render a "Solution ↗" link per row that
  opens in a new tab (`rel="noopener noreferrer"`). Until that field exists, omit the link
  rather than fabricate one. (Flagged as API feedback.)

### 6.3 Review affordances

- A **"Back to dashboard / history"** action (the submit already invalidated the progress
  query, so history is fresh). Review is terminal for the attempt - there is no "resume".
- The section is `aria-live="polite"` (already) so its arrival is announced; pair with the
  focus move in §8.3.

---

## 7. Edge Cases & States

### 7.1 Refresh / return mid-exam - [RISK - top priority]

**Current behavior:** state is `useReducer(runnerReducer, exam.num_problems, initRunner)` and
`startedAtRef = useRef(Date.now())`, both **in memory only**. A page refresh, accidental
back-navigation, or tab crash **wipes every answer and flag and restarts the clock from full
duration**. This directly threatens goals #3 ("never lose work") and #4 ("the timer is
sacred" - a refresh effectively *grants more time*, which is also an integrity problem).

**Recommended stance (ranked):**

1. **Server-authoritative attempt (best).** On exam start, create the attempt server-side and
   return a real `started_at`; the runner anchors `useCountdown` on the **server** deadline,
   not `Date.now()`. Autosave answers/flags (debounced PATCH, or localStorage mirror keyed by
   `attempt_id`) so a refresh **rehydrates** answers *and* resumes the **same** countdown.
   This fixes both data loss and the "refresh = free time" exploit at once.
2. **Local persistence (interim).** Mirror `RunnerState` + `startedAtRef` to `localStorage`
   under a key like `amc:attempt:{exam.id}`; on mount, if a non-expired snapshot exists, offer
   "Resume your in-progress exam?" and rehydrate (recompute `remaining` from the **stored**
   `startedAt`, so the clock keeps counting down rather than resetting). Clear on submit.
   Cheaper, no API change, but trusts the client clock.
3. **Explicit warning (floor).** At minimum, a `beforeunload` guard ("You have an exam in
   progress - leaving will lose your answers") so refresh/close isn't silent. This is a
   stopgap, not a fix.

This spec **recommends option 1 as the target and option 2 as the immediate mitigation**, and
calls the current "starts fresh" behavior out as the single biggest UX/integrity gap in the
runner.

### 7.2 Network failure on submit - [EXTENDS]

The mutation handles 409 but **not** generic failure: on a 5xx/timeout/offline, `onError`
falls through, the page stays `active`-but-the-attempt-may-or-may-not-have-landed, and the
student gets no feedback. This is especially dangerous on the **auto-submit** path (a blip at
the buzzer could lose the whole attempt).

**Recommended retry UX:**

- On non-409 error, **stay in a recoverable state**: show a non-dismissable banner "Couldn't
  submit - check your connection" with a **Retry** button that re-fires `submitMutation.mutate()`.
  Because the POST is idempotent server-side per attempt (a repeat returns 409 → existing
  result), retry is safe.
- **Do not** flip out of `submitting` into a dead end; either land on `review` (success/409) or
  surface Retry. For the **auto path**, keep the answers frozen and retry automatically a few
  times with backoff before showing the manual Retry, so a transient blip self-heals.
- Preserve answers in memory (and, with §7.1 option 2, in storage) across retries so the
  student never re-enters anything.
- If the failure is **401** (session expired), route to login and, on return, resubmit - never
  silently drop the attempt.

### 7.3 Very long equations - [EXTENDS]

KaTeX display blocks (`<Tex display>`) can overflow horizontally (long algebraic expressions,
big matrices). Spec: the `.question__body` allows **horizontal scroll within the block**
(`overflow-x: auto`) rather than letting a wide equation blow out the page layout or shove the
choices off-screen. Choices (inline `<Tex>`) wrap normally. Malformed TeX already degrades
gracefully - `throwOnError: false` renders a visible error string instead of crashing the
runner mid-exam (the `Tex.tsx` rationale), which the spec keeps.

### 7.4 Image-mode papers (AMC 10 scans) - [MATCHES] with polish

When `render_mode === 'image'`, `Question` renders `<img src={image_path}
alt="Problem {number}">` and **suppresses choice bodies**, showing only A–E letters (the scan
contains the options). Spec additions:

- The image must be **responsive** (`max-width: 100%`, never overflow) and ideally
  **zoomable** (tap/click to enlarge, or pinch on mobile) since scanned text can be small.
- **Loading & failure states**: a placeholder while the scan loads and a clear "Couldn't load
  this problem image" with a retry if `image_path` 404s - a missing image must not leave a
  blank, unanswerable question with the clock running.
- The radiogroup remains fully functional and keyboard-navigable on image papers (it already
  is), so a scan that fails to load still lets the student answer if they can read it elsewhere.

### 7.5 All-blank submission - [MATCHES] allowed, [EXTENDS] gentle nudge

`ExamSubmission.answers` may be all `null`; the server grades it (all blank → for `sixpoint`,
`blank * 1.5`; for `count`, 0). Nothing blocks it, and nothing should - a student may run out
of time. The manual confirm dialog (§5.1) naturally surfaces "0 of 25 answered" so an
*accidental* empty submit is caught, while the **auto** path submits whatever exists without
ceremony.

### 7.6 Voided problems in palette + review - [MATCHES]

A problem number in `ExamDetail.voided` is excluded from scoring (tech-spec). UX treatment:

- **Palette**: `.palette__cell--voided` renders the cell at reduced opacity with a
  `line-through`, and its `aria-label` says "voided" (the `statusLabel` helper short-circuits
  to "voided"). The student can still navigate to it. **[EXTENDS]** add a short tooltip/legend
  note "This problem was voided and doesn't count" so the strike-through isn't a mystery.
- **Question**: a voided problem should show a calm inline banner "This problem has been voided
  - it won't be scored," while still rendering it (a student may want to attempt it for
  practice). Whether to disable its radiogroup is a product call; the spec recommends leaving
  it answerable but visually marked, since voiding is a scoring concept, not a content one.
- **Review**: the row's Outcome is "∅ Void" (`outcome()` checks `voided` first), regardless of
  `ok`, and it is excluded from the Correct/Wrong/Blank tallies - consistent with the
  server's scoring.

### 7.7 State matrix (quick reference)

| Situation | Phase | What the student sees |
|---|---|---|
| Loading exam | n/a | `<Spinner label="Loading exam…">` |
| Load failed | n/a | `<ErrorState title="Could not load this exam">` |
| Taking the test | `active` | Full runner, editable, timer live |
| Pressed Submit | `active` → confirm | Confirm dialog (manual only) |
| Submitting | `submitting` | Frozen runner + "Submitting…" overlay |
| Submit failed (network) | `submitting` | Retry banner (§7.2) |
| Already submitted (409) | `submitting` → `review` | "Already submitted - here's your result" |
| Graded | `review` | `<ExamReview>`, key revealed |
| Time expired | `active` → `submitting` → `review` | "Time is up" announce → auto-submit → review |

---

## 8. Accessibility

Accessibility is a phase-3 acceptance item ("keyboard navigation and basic a11y pass") and is
woven through this spec; consolidated here.

### 8.1 Radiogroup semantics - [MATCHES]

The choices are a native `role="radiogroup"` fieldset of `<input type="radio">` with a group
`aria-label` ("Answer choices for problem {number}"). Native radios give correct arrow-key
roving, `checked` state, and announcement for free - the spec **keeps native radios** rather
than rebuilding with ARIA, which is the more robust choice. `disabled` on the fieldset (when
`frozen`) correctly removes them from the tab order during `submitting`/`review`.

### 8.2 `role="timer"` - [MATCHES] + [EXTENDS]

The visible timer is `role="timer"` with an `aria-label` ("Time remaining: M:SS") and
`aria-live="off"` (so it isn't read every second). The §3.5 milestone announcements live in a
**separate** visually-hidden polite/assertive region - keeping the `role="timer"` element
silent while still giving non-sighted students the urgency cues.

### 8.3 Focus management on phase changes - [EXTENDS]

Today, transitioning `active → submitting → review` swaps the whole subtree but does **not**
move focus, so a keyboard/SR user can be left with focus on a now-unmounted button. Spec:

- On entering **review**, move focus to the review `<h2>` ("Your result") and ensure it's the
  first thing announced (the section is already `aria-live="polite"`).
- On opening any **dialog/sheet** (confirm, palette sheet, help), trap focus inside and set
  initial focus to the safe default (Keep working / first cell / close button); on close,
  **return focus** to the trigger.
- On **auto-submit**, the assertive "Time is up" announcement covers the transition; focus
  then follows the review rule.

### 8.4 Announcements - [MATCHES] + [EXTENDS]

- Progress line `.runner__progress` is `aria-live="polite"` - answered-count changes are
  announced (already). Keep it, but ensure updates are not so chatty that rapid A→B→C changes
  spam the SR (debounce the announcement, not the state).
- Timer milestones per §3.5.
- Submit status ("Submitting your answers…", success → review, failure → "Couldn't submit,
  retry available") via a polite region so the student knows what's happening without watching.

### 8.5 Reduced motion - [EXTENDS]

There is **no `prefers-reduced-motion` handling today.** Spec: gate every non-essential
animation (the optional 1:00 timer "tick", any sheet slide-in, zebra/hover transitions) behind
`@media (prefers-reduced-motion: no-preference)`. Under reduced motion, urgency is conveyed
purely by the static shape/color/text changes (§3.4) and announcements - never by motion. This
matters doubly on an anxiety-sensitive, timed surface.

### 8.6 Contrast & color independence

All tokens used for state already have non-color partners (icons, text, shape): timer tiers
(§3.4), palette states (`line-through` for void, `⚑` for flag, outline for current), review
outcomes (✓/✗/∅ + words). Verify `--color-warn` (#9a5b00) and `--color-error` (#b00020) meet
4.5:1 against their backgrounds at the timer's weight/size during the phase-3 contrast pass.

---

## 9. Prioritized Recommendations

Ranked by impact on the five goals, with rationale and rough effort (S ≤ ~half-day,
M ≈ 1–2 days, L > 2 days incl. API work).

| # | Recommendation | Why it matters | Effort | Touches |
|---|---|---|---|---|
| **1** | **Persist in-progress attempt (survive refresh) + anchor timer on server `started_at`** | Today a refresh **wipes all answers and resets the clock** - the single biggest violation of "never lose work" *and* an integrity hole ("refresh = free time"). §7.1 option 1 is the real fix; option 2 (localStorage mirror) is the fast mitigation. | L (server) / M (localStorage interim) | `RunnerInner`, `useCountdown` anchor, attempt API |
| **2** | **Confirm-before-submit dialog (manual path only)** | Submit is irreversible and ends the attempt; one misclick loses everything. A dialog summarizing unanswered/flagged counts (from `answeredCount` + `flags`) is cheap insurance. Auto-submit deliberately skips it. | S–M | new dialog, `triggerSubmit` |
| **3** | **Network-failure retry on submit (esp. auto path)** | Only 409 is handled now; a blip at the buzzer can lose the whole attempt with no feedback. A Retry banner over a frozen `submitting` state, plus auto-retry-with-backoff on the timer path, closes a data-loss gap. | M | mutation `onError`, `RunnerInner` |
| **4** | **Make a 409 actually show the prior result** | The 409 branch dispatches `submitted` but `result` stays `null`, and the review branch needs `result !== null` → dead screen. Server should return the existing `ExamResultResponse` on repeat; client renders it. | S (client) + API | mutation, submit endpoint |
| **5** | **Timer urgency tiers + milestone aria-live (5-min / 1-min)** | Calm-by-default with caution@5:00 and warning@1:00 via **shape+text+ARIA** (not color), plus a sparse announcement schedule, gives every student (incl. SR users) honest "time's running out" cues without per-second chatter. Purely presentational - never changes the deadline. | M | `.runner__timer` styles, hidden live region, `RunnerInner` |
| **6** | **Keyboard shortcut layer + roving-tabindex palette** | None exists today. Letter keys to answer, `N/P` to navigate, `F` to flag, and a single-tab-stop palette make a power surface fast for keyboard and SR users and collapse 25 tab stops to one. | M | new key handler, `Palette` tabindex |
| **7** | **Mobile palette → drawer/sheet + sticky timer/controls** | On mobile the palette currently shoves the question below the fold and the timer can scroll away. A sheet + sticky header/footer keeps the clock visible and the question the hero. | M | layout, `Palette` sheet variant |
| **8** | **Review scannability: icons+words on Outcome, sticky header, wrong-vs-blank distinction, filters** | A 25-row table is the payoff; redundant-encoded outcomes (✓/✗/∅), a sticky `<thead>`, and an "Incorrect/Flagged/Blank" filter turn it from a wall of rows into something a student learns from. | M | `ExamReview`, styles |
| **9** | **Surface solution links in review** | Students want to *learn* from misses. `Exam.source_url` exists server-side but isn't exposed; add `solution_url`/`source_url` to the result and render "Solution ↗" per row. Omit until the field exists - don't fabricate. | M (API + client) | `ReviewItemResponse`/`ExamResultResponse`, `ExamReview` |
| **10** | **`prefers-reduced-motion` gating + focus management on phase change** | No reduced-motion handling today, and phase swaps don't move focus (SR/keyboard users get stranded). Gate animations; move focus to the review heading; trap/return focus in dialogs. | S–M | global CSS, `RunnerInner`, dialogs |
| **11** | **Stronger selected-choice visual + progress bar in header** | The OS radio dot is a weak "this is my answer" signal under time pressure; a left accent + fill and a thin answered-progress bar make current state pre-attentive. | S | `Question`/`.choice` styles, header |

### Sequencing note

Recommendations **1–4** are correctness/data-integrity and should land first (1 is the
headline). **5–8** are the experience upgrades that make the runner feel finished. **9–11** are
polish that compounds well with the phase-3 a11y/mobile pass already on the roadmap.

---

## Appendix A - Symbol & field cross-reference

| This spec calls it | Code / schema symbol | File |
|---|---|---|
| Reducer / state machine | `runnerReducer`, `RunnerState`, `RunnerAction`, `RunnerPhase`, `initRunner`, `answeredCount`, `clampIndex` | `frontend/src/features/exam/runnerState.ts` |
| Timer | `useCountdown` (`deadline`, `remaining`, `firedRef`, `onExpire`), `formatDuration` | `frontend/src/features/exam/useCountdown.ts` |
| Navigator | `Palette`, `statusLabel`, `.palette__cell--{answered,flagged,current,voided}` | `frontend/src/features/exam/Palette.tsx` |
| Question + choices | `Question`, `readChoices`, `stripDelimiters`, `role="radiogroup"` | `frontend/src/features/exam/Question.tsx` |
| Math render | `Tex` (`renderToString`, `throwOnError: false`) | `frontend/src/components/Tex.tsx` |
| Review | `ExamReview`, `outcome` | `frontend/src/features/exam/ExamReview.tsx` |
| Page / orchestration | `ExamRunnerPage`, `RunnerInner`, `triggerSubmit`, `submitMutation`, `startedAtRef`, `frozen` | `frontend/src/pages/ExamRunnerPage.tsx` |
| Submit wrapper / errors | `submitExam`, `getExam`, `ApiError` | `frontend/src/lib/endpoints.ts` |
| API: exam (key-free) | `ExamDetail`, `ProblemRead` (no `correct_answer`) | `docs/api/openapi.json` |
| API: submission | `ExamSubmission` (`answers`, `flags`, `time_used_sec`) | `docs/api/openapi.json` |
| API: graded result | `ExamResultResponse`, `ReviewItemResponse` (`n`, `your`, `correct`, `ok`, `voided`) | `docs/api/openapi.json` |

## Appendix B - Spec-vs-code status legend

- **[MATCHES]** the current implementation: §1.4/§3.1/§3.2 (timer contract & format),
  §4.1–4.3 (answer/flag/navigate), §5.2–5.4 (auto-submit, double-submit guards, 409 intent,
  payload), §6.1–6.2 (score breakdown + table columns), §7.4/§7.6 (image mode, voided).
- **[EXTENDS]** beyond current code: §2.2 (mobile sheet), §3.4–3.6 (urgency tiers, milestone
  announcements, submit overlay), §4.4 (keyboard model - none today), §5.1 (confirm dialog),
  §6.2 (filters, solution links - field doesn't exist), §7.1–7.3 (persistence, retry, equation
  overflow), §8.3/§8.5 (focus mgmt, reduced motion - none today).
- **[RISK]** current behavior to change: §7.1 refresh wipes state + resets clock (top issue);
  §5.4 a bare 409 can dead-end review; §7.2 unhandled non-409 submit failure.
