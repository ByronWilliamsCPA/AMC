---
title: "AMC Trainer - Component Library, Accessibility & Responsive Plan"
schema_type: common
status: draft
owner: core-maintainer
purpose: "Reusable component inventory, accessibility plan, and responsive plan for the AMC Trainer frontend."
tags:
  - design
  - frontend
  - accessibility
  - specifications
---

> **Status**: Design / implementation-ready. Authored against the as-built `frontend/src/` tree.
> **Scope**: Reusable component inventory, file/composition conventions, the accessibility plan,
> the responsive plan, and math-rendering notes.
> **Stack (locked)**: React 19 + TypeScript 5.7, Vite 6, CSS Modules + design tokens (CSS custom
> properties). No Tailwind, no component library. Math via KaTeX (`output: 'htmlAndMathml'`).
> Tone: clean & academic. Accessibility is a Phase-3 deliverable (keyboard navigation + a basic
> a11y pass), so the bar below is **WCAG 2.1 AA** and every requirement is written to be testable.

---

## 0. Current state (what this inventory is grounded in)

This is a **keep / refactor / add** inventory, not a greenfield list. Two facts shape every
recommendation below; both were verified against the tree:

1. **There are zero `*.module.css` files today.** All styling lives in one global stylesheet,
   `frontend/src/index.css`, addressed by global class names
   (`.runner__body`, `.palette__cell`, `.choice`, …). The "CSS Modules + co-located styles"
   convention in §2 is therefore a **planned migration**: as each component is built or
   refactored, its slice of `index.css` moves into a co-located `*.module.css`. `index.css`
   shrinks to **tokens + a tiny global reset only**.
2. **Several "obvious" primitives do not exist as components.** Buttons are raw `<button>`
   elements styled by a single global `button {}` rule; links use React Router `Link`/`NavLink`
   directly; text inputs and selects are raw `<input>`/`<select>` styled by global `input,
   select {}`. `Button`, `TextField`, `Select`, `Checkbox`, `Card`, `Badge`, and `Toast` are
   **add**. The exam/diagnostic/progress feature components already exist and are mostly **keep**
   with small refactors.

What already exists (read for grounding):

| Path | Role |
|------|------|
| `components/Tex.tsx` | KaTeX wrapper (`MathRenderer`), memoized, `htmlAndMathml` |
| `components/States.tsx` | `Spinner`, `ErrorState`, `EmptyState` |
| `components/Layout.tsx` | App shell: header nav (role-aware) + `<Outlet/>` |
| `components/ErrorBoundary.tsx` | Top-level render-crash boundary |
| `features/exam/Palette.tsx` | Question navigator grid |
| `features/exam/Question.tsx` | One problem + A–E radiogroup |
| `features/exam/ExamReview.tsx` | Post-submit score + per-problem table |
| `features/exam/useCountdown.ts` | Absolute-deadline timer hook + `formatDuration` |
| `features/exam/runnerState.ts` | Pure runner reducer (answers/flags/nav/phase) |
| `features/progress/ProgressView.tsx` | Dashboard: recommendation, algebra-gate warning, 2 tables |
| `pages/*` | Route components (lists, runners, auth, invite, progress) |

Existing accessibility patterns to **preserve** (the app already does these, and the inventory
codifies them rather than reinventing them):

- Status conveyed by **text + ARIA, never colour alone** - the explicit convention in the
  `States.tsx` and `Palette.tsx` headers. The palette cell label is e.g.
  `"Question 2: unanswered, flagged"`, not just a colour.
- A–E choices are a **labelled `role="radiogroup"`** (`Question.tsx`, a `<fieldset>` that also
  carries the native `disabled` freeze).
- The timer is `role="timer"` with `aria-live="off"` (correct - see §3.3 for why per-second
  polite announcements would be a screen-reader DoS).
- `:focus-visible { outline: 3px solid var(--color-primary); outline-offset: 2px }` is **global**
  in `index.css` - every focusable element already has a visible ring.
- `.visually-hidden` utility exists for screen-reader-only labels (used in `DiagnosticRunnerPage`).
- Errors use `role="alert"` (`ErrorState`, `ErrorBoundary`, form errors, the algebra warning).

**As-built deviations worth flagging (do not "fix" silently):**

- The tech-spec names **axios** for the API client, but the code generates a **fetch** client
  (`@hey-api/client-fetch`, see `lib/api.ts` /
  `client/`). This doc follows the as-built fetch client. *(Tracked
  as template/spec drift; see `docs/template_feedback.md` if it needs reconciling.)*
- KaTeX is described as "auto-render" in the spec, but `Tex.tsx` deliberately uses
  `renderToString` inside `useMemo` instead of the global `renderMathInElement` scanner (it
  fights React reconciliation). The component approach is correct and stays. See §5.

---

## 1. Component inventory

Grouped: **Primitives → Form controls → Feedback/Status → Data display → Exam-runner-specific →
Layout**. Each entry gives **purpose · key props (TS-ish) · states · a11y (role/ARIA/keyboard) ·
token groups consumed · keep/refactor/add**.

States legend: `default · hover · focus · active · disabled · loading · error` (only the
applicable subset is listed per component).

### 1.1 Primitives - `src/components/ui/`

#### `Button` - **ADD**

- **Purpose**: The single styled action element. Replaces the global `button {}` rule and the
  one-off `.runner__submit` / `.link-button` styles so every button is consistent and
  token-driven. Used by the runner controls, filter bar, auth/invite forms.
- **Props**:

  ```ts
  interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'link'  // default 'secondary'
    size?: 'sm' | 'md'                                     // default 'md'; 'md' >= 44px target
    loading?: boolean        // shows spinner text, sets aria-busy, disables
    iconOnly?: boolean       // requires aria-label; enforces square min-target
  }
  ```

- **States**: default, hover, focus (inherits global `:focus-visible`), active, disabled
  (`opacity .5; cursor not-allowed`, native `disabled`), loading (`aria-busy="true"`, disabled,
  label → `"Submitting…"`).
- **A11y**: always real `<button type="button|submit">` (never a clickable `<div>`). `iconOnly`
  **must** have `aria-label`; lint via `jsx-a11y`. Toggle buttons keep the existing
  `aria-pressed` pattern (Flag button, filter chips). `'link'` variant is for in-flow actions
  that are not navigation (e.g. "Clear answer"); true navigation uses `Link` (§1.2). Disabled
  buttons must not be the only way to learn *why* they're disabled (pair with adjacent text where
  relevant). Min target 44×44 CSS px for `md` (WCAG 2.5.5 / 2.5.8).
- **Tokens**: color (`--color-primary`, `--color-primary-fg`, `--color-surface`, `--color-border`,
  `--color-fg`), spacing (`--space-2/3`), radius (`--radius`), focus-ring token (new, §4.1).

#### `Link` / `NavLink` - **KEEP (wrap thinly)**

- **Purpose**: Client-side navigation. The header already uses React Router `NavLink`
  (`Layout.tsx`); lists use `Link` (`ExamListPage`, `DiagnosticListPage`).
- **Props**: pass-through of `react-router-dom` `LinkProps` / `NavLinkProps`. Optional thin
  re-export `ui/Link.tsx` that applies token-based link styles and an `aria-current="page"`-driven
  active style for `NavLink` (router sets this automatically).
- **States**: default, hover (underline), focus, visited (academic tone: keep visited
  distinguishable but subtle), active route (`NavLink` → `aria-current="page"`).
- **A11y**: links navigate, buttons act - do not blur the two. `NavLink` active state must not be
  **colour-only**; add weight/underline so it satisfies 1.4.1. External links (none yet) would
  need `rel="noopener"` + a visible "opens externally" affordance.
- **Tokens**: color (`--color-primary`), spacing, focus-ring.

#### `VisuallyHidden` - **KEEP (promote utility → component)**

- **Purpose**: Screen-reader-only text. The `.visually-hidden` class already exists in `index.css`
  and is used inline; promote to `<VisuallyHidden>` for ergonomics (skip-link target text,
  table-context labels, "current question" announcements).
- **A11y**: must remain focusable-safe (the skip link uses a `:focus` reveal, §3.6). Tokens: none.

### 1.2 Form controls - `src/components/ui/`

#### `TextField` - **ADD** (used by Login, Register, Invite, Diagnostic typed answers)

- **Purpose**: Label + input + error message as one accessible unit. Today each form re-wires
  `<label htmlFor>` + `<input id>` + a `role="alert"` `<p>` by hand (`LoginPage`, `RegisterPage`,
  `InvitePage`, `DiagnosticRunnerPage`). Centralise the wiring so labelling/error association is
  correct by construction.
- **Props**:

  ```ts
  interface TextFieldProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'id'> {
    label: string
    name: string
    error?: string          // wires aria-invalid + aria-describedby
    hint?: string           // e.g. "Password (8+ characters)"
    visuallyHiddenLabel?: boolean   // for the diagnostic typed-answer case
  }
  ```

- **States**: default, focus, disabled, **error** (`aria-invalid="true"`, red border + `--color-error`
  text, message in an element referenced by `aria-describedby`).
- **A11y** (WCAG 1.3.1, 3.3.1, 3.3.2, 4.1.3): generate a stable `id` (`useId`); `<label htmlFor>`
  bound to it; `hint` and `error` each get ids and are joined into `aria-describedby`; set
  `aria-invalid` only when `error` is present; preserve native `type`, `required`, `minLength`,
  `autoComplete` (the auth forms already set `autoComplete="username|current-password|new-password"`;
  keep). Error text must be **programmatically associated**, not just visually adjacent.
- **Tokens**: color (border/error/fg/muted), spacing, radius, focus-ring.

#### `Select` - **ADD** (Invite role picker; exam-list contest filter could migrate)

- **Purpose**: Labelled native `<select>` wrapper (`InvitePage` role picker is the live case).
- **Props**: `{ label, name, options: {value,label}[], value, onChange, error?, hint? }`.
- **States**: default, focus, disabled, error.
- **A11y**: native `<select>` (keyboard + SR support for free); `<label htmlFor>` association;
  no custom listbox unless a hard requirement appears (a custom one must re-implement
  `role="listbox"`/`option`, type-ahead, and arrow-key semantics - avoid for now).
- **Tokens**: color, spacing, radius, focus-ring.

#### `Checkbox` - **ADD / refactor** (diagnostic self-mark "I solved this correctly")

- **Purpose**: Labelled boolean. Live use: the self-mark checkbox in `DiagnosticRunnerPage`
  (`.diagnostic__selfmark`).
- **Props**: `{ label: ReactNode, name, checked, onChange, disabled? }`.
- **States**: default, checked, focus, disabled.
- **A11y**: native `<input type="checkbox">` inside a `<label>` (clickable label, ≥44px hit area).
  Checked state must be conveyed beyond colour (the native check glyph does this). 1.3.1 / 2.5.5.
- **Tokens**: color, spacing, focus-ring.

#### `RadioGroup` (the A–E answer choices) - **KEEP / refactor** ← critical component

- **Purpose**: The exam answer choices. Lives today inside
  `features/exam/Question.tsx` as a `<fieldset
  role="radiogroup">` of `<label><input type="radio">…</label>`. Extract the group mechanics into
  a reusable `ui/RadioGroup` so the diagnostic and any future MCQ reuse it; `Question` keeps the
  KaTeX choice rendering.
- **Props**:

  ```ts
  interface RadioGroupProps {
    legend: string                       // -> aria-label / <legend> ("Answer choices for problem 7")
    name: string                         // native grouping ("problem-7")
    value: string | null                 // selected letter or null
    options: { value: string; label: ReactNode }[]  // A–E with KaTeX-rendered labels
    disabled?: boolean                   // exam freeze on submit
    onChange: (value: string) => void
  }
  ```

- **States**: default, hover (row), focus (the checked radio, or first if none), checked, disabled
  (frozen after submit). No "error" state for the exam (blank is a valid answer).
- **A11y** (WCAG 2.1.1, 1.3.1, 4.1.2): native radios give **roving focus and arrow-key selection
  for free** - Tab moves into the group, Arrow keys move between options, Space/Enter selects.
  Keep `name` per problem so only one is checked. `<fieldset disabled>` freezes the whole group
  on submit (already done) and is exposed to AT. The visible A–E letter must be inside the label
  so screen-reader users hear "A. <math>". Do **not** convert to `tabindex`-managed buttons - the
  native radiogroup is the accessible default and is simpler. (Contrast the *palette*, which is
  intentionally a roving-tabindex grid - see §1.5 / §3.1.)
- **Tokens**: color, spacing (`--space-2`), radius, border, focus-ring.

### 1.3 Feedback / status - `src/components/ui/`

#### `Spinner` / `LoadingState` - **KEEP** (`States.tsx`)

- **Purpose**: Async-pending indicator. Currently `<output className="spinner" aria-live="polite">`.
- **Props**: `{ label?: string }` (default `"Loading…"`).
- **States**: loading only.
- **A11y**: `<output>` has implicit `role="status"` (polite live region) - text label ("Loading
  exam…") is the announcement, so it works without colour/animation. **If** a spinning glyph is
  added later, it must `@media (prefers-reduced-motion: reduce)` to a static state (§3.7). Keep the
  text-first design.
- **Tokens**: color (`--color-muted`).

#### `ErrorState` - **KEEP** (`States.tsx`)

- **Purpose**: Inline error block (`role="alert"`). Used by every page's `isError` branch and the
  diagnostic submit failure.
- **Props**: `{ title?: string; children?: ReactNode }`.
- **States**: error only.
- **A11y**: `role="alert"` (assertive live region) - announced on mount. Keep the title as **text**
  (3.3.1). Don't render multiple simultaneously-mounting alerts (assertive pile-up); prefer one.
- **Tokens**: color (`--color-error`), spacing, radius.

#### `EmptyState` - **KEEP** (`States.tsx`)

- **Purpose**: "No data yet" messaging (empty exam list, no contests/diagnostics taken).
- **Props**: `{ children: ReactNode }`.
- **States**: default.
- **A11y**: plain text; muted colour must still meet 4.5:1 against background (verify
  `--color-muted #5b5b73` on `--color-bg #fff` and on `--color-surface #f5f6fa`, §3.5).
- **Tokens**: color (`--color-muted`).

#### `Alert` / `Callout` (incl. the algebra-gate warning) - **ADD** (generalise `progress__warning`)

- **Purpose**: A standing, non-transient message box with severities. The motivating case is the
  **algebra-gate warning** (`ProgressView`, `data.algebra_warning`, currently a bare `<p
  role="alert" className="progress__warning">`). Generalise to `info | success | warning | error`.
- **Props**:

  ```ts
  interface AlertProps {
    severity: 'info' | 'success' | 'warning' | 'error'
    title?: string
    children: ReactNode
    role?: 'status' | 'alert'   // default: 'alert' for error/warning, 'status' otherwise
  }
  ```

- **States**: one per severity (visual), plus an optional dismissible variant (not needed yet).
- **A11y** (1.4.1, 4.1.3): **colour is never the only signal** - render a per-severity text/icon
  prefix ("Warning:", "Error:") and an `aria-hidden` icon, with the severity word visible. Use
  `role="alert"` for error/warning that appear in response to user action; `role="status"` for
  passive info. The algebra-gate warning is content present on load → `role="status"` is acceptable
  there (it is not a response to an action); the current `role="alert"` also passes but will
  announce on every dashboard load - prefer `status` for that specific instance.
- **Tokens**: color (`--color-warn`, `--color-error`, `--color-ok`, plus an `info` token to add
  in §4.1), spacing, radius, border.

#### `Badge` / `Tag` (verdict, voided, role) - **ADD**

- **Purpose**: Compact status pills. Cases found in the data:
  - **Verdict** (`ProgressView` diagnostics table → `verdict`, e.g. PASS/REVIEW/FAIL; diagnostic
    result `result.verdict.toUpperCase()`).
  - **Voided** (`ExamReview` outcome "Void"; palette voided cells).
  - **Role** (`InvitePage` student/coach/admin).
- **Props**: `{ tone: 'neutral' | 'success' | 'warning' | 'danger' | 'info'; children: ReactNode }`.
- **States**: default (static).
- **A11y** (1.4.1): the badge's **text is the meaning** (e.g. "Void", "PASS") - tone colour is
  decorative. Never ship a colour-only dot. If a badge needs extra context for SR users (e.g. a
  bare "⚑"), add `VisuallyHidden` text. Ensure badge text meets 4.5:1, or 3:1 if it qualifies as a
  large/UI label - verify per tone (§3.5).
- **Tokens**: color (tone + fg), spacing (`--space-1/2`), radius.

#### `Toast` (optional) - **ADD (deferred)**

- **Purpose**: Transient confirmations (e.g. "Invite link copied", future autosave). **Not
  required for Phase 3** - current confirmations are inline (`InvitePage` "Share this link once"
  block, `aria-live="polite"`). If added: a single app-level `aria-live="polite"` region (a
  `role="status"` container) that toasts write into; never trap focus; auto-dismiss must not be the
  only way to read it (WCAG 2.2.1 timing). Recommend deferring until a concrete need.
- **Tokens**: color, spacing, radius, z-index (new token, §4.1), focus-ring.

### 1.4 Data display - `src/components/ui/`

#### `Card` - **ADD**

- **Purpose**: A bordered content container with consistent padding/radius. Primary driver: the
  **responsive progress dashboard**, where wide tables collapse to **stacked cards** on mobile
  (§4.3). Also useful to upgrade the exam/diagnostic **list rows** (`.exam-list li`) into tappable
  cards.
- **Props**: `{ as?: 'article' | 'section' | 'li'; children: ReactNode; interactive?: boolean }`.
- **States**: default; if `interactive`, hover + focus-within (the focus ring comes from the
  inner link/button, not the card).
- **A11y**: a card is presentational - **do not** make the whole card a click target with a
  nested interactive child (double-activation / nesting issues). One real link/button inside,
  card stretches its hit area via `::after` overlay if desired (keep keyboard focus on the link).
  Use a meaningful element (`<article>`/`<li>`), not a bare `<div>`, when it represents an item.
- **Tokens**: color (surface/border), spacing (`--space-3/4`), radius.

#### `Table` (review + progress) - **KEEP / refactor into a shared shell**

- **Purpose**: Tabular data. Three live tables share structure and the `.review__table /
  .progress__table` styles: `ExamReview` per-problem table, and the two `ProgressView` tables
  (contest history, diagnostics). Extract a thin `ui/Table` (semantic `<table>` with a slot for
  `<caption>`, `<thead scope="col">`, `<tbody>`) **plus** the responsive stack behaviour (§4.3).
- **Props**: `{ caption: string; columns: Column[]; rows: Row[]; stackOnMobile?: boolean }` (or a
  composable `<Table><Table.Head/>…` API - implementer's choice; semantics are the contract).
- **States**: default; empty handled by `EmptyState` (already done), not an empty `<tbody>`.
- **A11y** (WCAG 1.3.1): real `<table>` with `<caption>` (the review table already has
  `<caption>Per-problem review</caption>` - **add captions to the two progress tables**, which
  currently lack them), `<th scope="col">` headers (already present), and row keys. On the mobile
  **stacked-card** rendering, each "row card" must keep its header→value association - use a
  CSS technique that preserves DOM table semantics (e.g. `data-label` pseudo-content) **or** an
  explicitly labelled definition-list per row; do not drop the header text. Never use a `<table>`
  for layout.
- **Tokens**: color (border/muted), spacing.

#### `MathRenderer` (KaTeX wrapper) - **KEEP** (`components/Tex.tsx`, exported as `Tex`)

- See §5 for full a11y + responsive treatment. Inventory summary:
- **Purpose**: Render a LaTeX string with KaTeX, React-safely.
- **Props**: `{ tex: string; display?: boolean }`.
- **A11y**: `output: 'htmlAndMathml'` already emits a MathML tree for AT alongside the visual HTML.
  **Refactor needed**: the visual HTML must be hidden from AT (`aria-hidden`) so screen readers
  read the MathML once, not the visual spans too - KaTeX does this internally for its own spans,
  but our wrapping `<span data-testid="math">` should not add a conflicting role. Wide-equation
  overflow handling is a §5 requirement.
- **Tokens**: typography/color inherited; KaTeX CSS imported once in `main.tsx`.

### 1.5 Exam-runner-specific - `src/features/exam/`

#### `Timer` / `Countdown` - **KEEP** (`useCountdown.ts` hook + `.runner__timer` markup)

- **Purpose**: Drift-free countdown from an **absolute deadline** (`startedAt + durationSec`),
  auto-submitting once at zero. The hook is correct and unit-tested
  (`useCountdown.test.ts`); the `#CRITICAL: timing` rationale (no decrement, survives a
  backgrounded tab) must be preserved.
- **Surface**: `useCountdown(startedAtMs, durationSec, onExpire) → { remaining, expired }` and
  `formatDuration(s) → "M:SS" | "H:MM:SS"`. Recommend extracting the **visual** chip into a small
  `<Timer remaining={…} />` presentational component so the runner JSX is cleaner and the chip is
  reusable (diagnostics could show elapsed time).
- **States**: running, (visually) warn under a threshold (e.g. ≤60s → `--color-warn`), expired.
- **A11y** (this is subtle - see §3.3): the visible timer is `role="timer"` with **`aria-live="off"`**
  (correct: a per-second polite region would flood a screen reader). Announce **milestones** instead
  via a separate polite region ("5 minutes remaining", "1 minute remaining"). The warn threshold
  must not be **colour-only** - pair with the text milestone announcement and optionally a "Time
  almost up" visible label. `font-variant-numeric: tabular-nums` is already set so the digits don't
  jitter.
- **Tokens**: color (`--color-fg`, `--color-warn`), typography (size/weight), `tabular-nums`.

#### `Palette` / `QuestionNavigator` - **KEEP / refactor for roving tabindex** ← critical

- **Purpose**: Grid of problem numbers showing answered / flagged / current / voided
  (`Palette.tsx`). Renders as `<nav
  aria-label="Question navigator"><ul>` of `<button>`s, each with
  `aria-label="Question N: <status>"` and `aria-current` on the current one. Status is text +
  shape, not colour (answered = filled, flagged = thick border + "⚑", voided = strikethrough +
  dimmed). This is the model the rest of the app should imitate.
- **Props**: `{ state: RunnerState; voided: number[]; onSelect: (index) => void }` (keep). Add
  optional `orientation`/grid metadata only if needed for the roving model.
- **States** per cell: default, hover, focus, **current** (`aria-current="true"` + outline),
  answered, flagged, voided. (Disabled is **not** used - voided cells stay focusable/announced.)
- **A11y refactor** (WCAG 2.1.1, 2.4.3, 4.1.2) - the one real keyboard upgrade in the runner:
  today every cell is in the tab order (25–30 Tab stops to cross the palette). Convert to a
  **roving-tabindex grid**:
  - Wrap the grid in `role="grid"` (or keep `<nav>` + add a `role="grid"` inner list); cells are
    `role="gridcell"` buttons. Exactly **one** cell has `tabIndex={0}` (the current question);
    all others `tabIndex={-1}`.
  - **Arrow keys** move focus within the grid (Left/Right by one; Up/Down by one row given the
    `repeat(5, …)` columns); **Home/End** to first/last; **Enter/Space** activates `onSelect`.
    Manage focus imperatively (refs) so DOM focus follows the roving index.
  - Tab/Shift-Tab enters/leaves the whole palette as a **single stop** - restoring the keyboard
    flow: Tab from header → palette (one stop) → question radiogroup → controls.
  - Keep `aria-current` and the full text labels. Update `Palette.test.tsx` to assert arrow-key
    movement and single-tab-stop behaviour (§3.8).
- **Tokens**: color (answered/flag/current/voided), spacing (`--space-1`), radius, focus-ring;
  layout uses `aspect-ratio: 1` cells in a `repeat(5, 1fr)` grid (touch-sizing in §4.2).

#### `Question` - **KEEP** (`features/exam/Question.tsx`)

- **Purpose**: Renders one problem (image-mode `<img alt>` or latex-mode `<Tex display>`) + the
  A–E `RadioGroup` + a "Clear answer" link-button. Already accessible; once `ui/RadioGroup` is
  extracted, `Question` composes it.
- **States**: default, disabled (frozen on submit via `<fieldset disabled>`).
- **A11y**: problem heading is an `<h2>` ("Problem N") - preserve the heading order under the
  runner `<h1>`. Image problems have real `alt` ("Problem N"); if a richer description is
  available later, use it. Choice labels keep the visible A–E letter (so the verbal answer and the
  paper match).
- **Tokens**: spacing, border, radius, color.

#### `ExamReview` - **KEEP** (`features/exam/ExamReview.tsx`)

- **Purpose**: The only place the answer key is shown; renders score `<dl>` + per-problem `<table>`.
- **A11y**: wrapper is `aria-live="polite"` so the result is announced when it replaces the runner
  (good - pairs with focus management in §3.2). Outcome column is **text** ("Correct"/"Incorrect"/
  "Void"), not colour. If colour is added to outcomes, keep the word and meet 3:1/4.5:1.
- **Tokens**: color, spacing.

### 1.6 Layout - `src/components/`

#### `Layout` / `AppShell` - **KEEP / refactor (add skip link + focus mgmt)**

- **Purpose**: Header (role-aware `NavLink`s: Tests, Diagnostics, Progress, Invite-if-staff, user +
  Sign out) over a routed `<main>` (`Layout.tsx`).
- **Props**: none (reads `useAuth`). Renders `<Outlet/>`.
- **A11y refactors** (WCAG 2.4.1, 2.4.3): the header `<nav aria-label="Primary">` and
  `<main>` already exist. **Add**: (1) a **skip link** as the first focusable element →
  `#main-content` (§3.6); give `<main id="main-content" tabIndex={-1}>`; (2) **route-change focus
  management** - on navigation, move focus to `<main>` (or the page `<h1>`) and announce the new
  page title in a polite region (§3.2). Ensure exactly one `<h1>` per page (pages provide it;
  the shell must not add a second).
- **Tokens**: color (border/fg/primary), spacing, `--maxw` (content max-width), `--font`.

#### `ErrorBoundary` - **KEEP** (`components/ErrorBoundary.tsx`)

- **Purpose**: Top-level render-crash fallback (`role="alert"`, reload button). Keep. Consider
  routing render-crashes to a focus-managed message so AT users aren't stranded on a silently
  swapped tree.

---

## 2. Composition & file layout

### 2.1 Directory layout

```
src/
  components/
    ui/                      # NEW home for primitives (presentational, app-agnostic)
      Button.tsx             Button.module.css
      Link.tsx               Link.module.css
      TextField.tsx          TextField.module.css
      Select.tsx             Select.module.css
      Checkbox.tsx           Checkbox.module.css
      RadioGroup.tsx         RadioGroup.module.css      # extracted from Question
      Spinner.tsx            ...                          # moved out of States.tsx
      ErrorState.tsx
      EmptyState.tsx
      Alert.tsx              Alert.module.css
      Badge.tsx              Badge.module.css
      Card.tsx               Card.module.css
      Table.tsx              Table.module.css
      VisuallyHidden.tsx
      index.ts               # barrel: re-export the primitives
    Tex.tsx                  # MathRenderer (cross-cutting; may stay at components/ root)
    Layout.tsx               Layout.module.css
    ErrorBoundary.tsx        ErrorBoundary.module.css
  features/                  # feature-scoped components (own state/data shape)
    exam/
      Palette.tsx            Palette.module.css
      Question.tsx           Question.module.css
      ExamReview.tsx         ExamReview.module.css
      Timer.tsx              # NEW presentational chip over useCountdown
      useCountdown.ts  runnerState.ts  (+ *.test.*)
    progress/
      ProgressView.tsx       ProgressView.module.css
  pages/                     # route components - compose ui/* + features/*
  index.css                  # SHRINKS to: tokens (:root) + minimal reset/util only
```

**Rule of thumb**: `components/ui/*` = reusable, presentational, no feature/data knowledge.
`features/<x>/*` = knows a feature's data shape (`RunnerState`, `ProgressResponse`) and composes
primitives. `pages/*` = routing + data fetching (React Query) + composition; pages should contain
**no bespoke styling** that belongs in a component.

### 2.2 CSS Modules co-location convention

- Every component gets a sibling `Name.module.css`; import as
  `import styles from './Name.module.css'` and reference `className={styles.root}`.
- Class names inside a module are **local/camelCase** (`styles.root`, `styles.isCurrent`); the
  global BEM-ish names in `index.css` (`palette__cell--current`) become local
  (`styles.cellCurrent`). This removes the global-namespace coupling that exists today.
- **Tokens stay global** - components read `var(--color-primary)` etc.; modules never redefine
  tokens, only consume them. The `:root {…}` token block and the global reset (`box-sizing`,
  `body`, `:focus-visible`, `.visually-hidden`) remain in `index.css`. KaTeX CSS stays imported
  once in `main.tsx`.
- **Migration path** (incremental, low-risk): build new primitives module-first; when refactoring
  an existing component, cut its rules out of `index.css` into the co-located module in the same
  PR. Track progress by `index.css` line count trending toward "tokens + reset only".

### 2.3 Variants without a library (props → className)

No `cva`/Tailwind. Express variants by mapping props to local class names. Two sanctioned patterns,
both already prefigured by the codebase's `[…].filter(Boolean).join(' ')` style in `Palette.tsx`:

```ts
// (a) lookup map - preferred for enumerated variants
import styles from './Button.module.css'
const VARIANT: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary: styles.primary, secondary: styles.secondary,
  ghost: styles.ghost, link: styles.link,
}
const cx = (...c: (string | false | undefined)[]) => c.filter(Boolean).join(' ')

function Button({ variant = 'secondary', size = 'md', loading, className, ...rest }: ButtonProps) {
  return (
    <button
      className={cx(styles.root, VARIANT[variant], size === 'sm' && styles.sm, className)}
      aria-busy={loading || undefined}
      disabled={rest.disabled || loading}
      {...rest}
    />
  )
}
```

- Add **one tiny `cx` helper** (≈3 lines, in `lib/cx.ts`) - do not pull in `clsx`/`classnames` for
  this; it keeps the dependency surface (and the security review) minimal.
- For **state-driven** styling that the DOM already carries, prefer **attribute selectors over
  extra classes** - the app does this well today: `button[aria-pressed='true']`,
  `:focus-visible`, `<fieldset disabled>`. Style `[aria-current='true']`, `[aria-invalid='true']`,
  `[aria-busy='true']` in the module rather than threading a boolean prop → class. This keeps the
  ARIA state and the visual state from drifting (1.4.1 / 4.1.2 win for free).

---

## 3. Accessibility plan (testable, mapped to WCAG 2.1 AA)

`eslint-plugin-jsx-a11y` is already wired (`recommended` ruleset, see
`frontend/eslint.config.js`). That catches static markup
defects (missing `alt`, label-less controls, bad roles). It does **not** test behaviour - the plan
below adds the runtime/keyboard contract and the axe checks.

### 3.1 Keyboard model - exam runner (the hardest screen)

Target tab order on the runner page, top to bottom:

1. **Skip link** (§3.6) → jumps to `#main-content`.
2. **Header nav** (`NavLink`s) - standard tab sequence.
3. **Timer / progress** - not focusable (status only).
4. **Palette** - **one** tab stop (roving-tabindex grid, §1.5). Arrows move between cells,
   Home/End jump, Enter/Space selects → `goto`. *Today this is 25–30 stops; the refactor is the
   main keyboard deliverable.* (WCAG 2.1.1, 2.4.3.)
5. **Question radiogroup** - Tab enters the group; **Arrow keys** choose A–E (native radio
   semantics); Space/Enter selects. "Clear answer" link-button is the next stop when present.
6. **Controls** - Previous, Flag (`aria-pressed`), Next, Submit - each a tab stop, all reachable;
   disabled buttons are skipped by browsers (acceptable) but their disabled reason is visible.
   **Flag and Submit are keyboard-reachable** (requirement met by being real `<button>`s).

- **No keyboard trap** anywhere (WCAG 2.1.2) - verify focus can always leave the palette via Tab.
- **No positive `tabindex`** (only `0`/`-1`). Lint + a test assert this.

### 3.2 Focus management (route changes & view swaps)

- **Route change**: move focus to `<main id="main-content" tabIndex={-1}>` (or the page `<h1>`) on
  every navigation, and announce the page name in a polite region. Without this, SR/keyboard users
  stay on the old (now-unmounted) control after a `Link` activates. Implement in `Layout` via a
  `useEffect` on `location.pathname`. (WCAG 2.4.3.)
- **Runner → review swap** (not a route change - `ExamRunnerPage` swaps `RunnerInner` for
  `ExamReview` in place): on submit success, **move focus to the review heading** ("Your result")
  and rely on its `aria-live="polite"` wrapper to announce. Same for the diagnostic result view.
- **Dialogs**: none today. **If** a confirm-submit dialog or the mobile palette **drawer** (§4.2)
  is added, it must: trap focus while open, restore focus to the trigger on close, close on
  `Esc`, and use `role="dialog"`/`aria-modal="true"` with a labelled heading. (WCAG 2.4.3, 2.1.2.)
- **Async errors**: `ErrorState`/`role="alert"` announces on mount; additionally move focus to the
  error (or its retry button) for keyboard users when an action fails (e.g. submit error).

### 3.3 `aria-live` usage (the announcement contract)

| Surface | Region politeness | Cadence / rule |
|---------|-------------------|----------------|
| **Timer** (`role="timer"`) | `aria-live="off"` (keep) | **Never** per-second. The visible chip is silent to AT. |
| **Timer milestones** | separate `role="status"` (polite) | Announce at thresholds only: 10:00, 5:00, 1:00, 0:30, "Time's up". Drives the auto-submit narration. |
| **Answered count** (`.runner__progress`) | `aria-live="polite"` (keep) | Announces "N of M answered" on change - already wired; polite + low-frequency is fine. |
| **Submit / grade result** (`ExamReview`, diagnostic result) | `aria-live="polite"` (keep) + focus move | Announced when the result view mounts. |
| **Async errors** (`ErrorState`) | `role="alert"` (assertive) | On mount; one at a time. |
| **Algebra-gate warning** | `role="status"` (recommend) | Present on load → polite, not assertive (it isn't a response to an action). |
| **Toast** (if added) | single app-level `role="status"` (polite) | Serialise messages; never assertive. |

Rationale for the timer split is the key call: WCAG 4.1.3 wants status messages announced, but a
1-second polite region re-announces ~constantly and renders the page unusable with a screen reader.
The milestone region satisfies the intent without the flood.

### 3.4 Colour is not the only signal (WCAG 1.4.1) - enforce everywhere

The app already follows this; the rule is now **mandatory and tested** for new components:

- Palette: answered/flagged/current/voided each have a **non-colour** cue (fill / thick border +
  "⚑" / outline + `aria-current` / strikethrough) **and** the full text label. ✔ (keep)
- Timer warn threshold: must add a **text** cue ("1 minute remaining"), not just red. (add)
- `Alert`/`Badge`: severity/tone carries a **word** ("Warning:", "PASS", "Void"), colour is
  decorative. (build this in)
- Form errors: red **plus** message text **plus** `aria-invalid` + `aria-describedby`. (TextField)
- `NavLink` active: weight/underline in addition to colour. (add)
- **Test**: a lint convention + review checklist item; spot-check with axe (axe flags some, not
  all, colour-only cases - human review covers the rest).

### 3.5 Colour contrast (WCAG 1.4.3 / 1.4.11)

Verify the token palette meets **4.5:1** for normal text, **3:1** for large text and UI component
boundaries/focus rings, against the backgrounds it's actually used on
(`--color-bg #fff`, `--color-surface #f5f6fa`):

- Audit pairs: `--color-fg #1a1a2e`, `--color-muted #5b5b73`, `--color-primary #2d4ea2` (+ on
  primary, `--color-primary-fg #fff`), `--color-ok #1b7f4b`, `--color-warn #9a5b00`,
  `--color-error #b00020`, `--color-border #d4d7e0` (focus/affordance boundaries need 3:1).
- `--color-muted` on `--color-surface` is the most likely near-miss - verify explicitly.
- **Action**: run an automated contrast pass (axe includes colour-contrast) on a representative
  rendered page per route; record results; fix any token that fails by darkening, not by
  case-by-case overrides.

### 3.6 Skip link (WCAG 2.4.1)

- Add as the **first** child of `Layout`: `<a className={styles.skipLink}
  href="#main-content">Skip to main content</a>`, visually-hidden until `:focus` (reuse the
  `.visually-hidden` reveal pattern but make it focusable). Target `<main id="main-content"
  tabIndex={-1}>`. Test: first Tab from page load focuses the skip link; activating it moves focus
  into `<main>`.

### 3.7 Reduced motion (WCAG 2.3.3 best-practice / future-proofing)

- Add a global `@media (prefers-reduced-motion: reduce)` block that disables non-essential
  transitions/animations (drawer slide, any future spinner rotation, focus transitions). Today
  there is **no** motion, so this is a guardrail: any animation a component introduces **must**
  honour the query. Add `--reduced-motion`-aware transitions via a tokenised duration that the
  media query zeroes.

### 3.8 Form labelling & error association (WCAG 1.3.1, 3.3.1, 3.3.2, 3.3.3)

- Every input has a programmatic label: visible `<label htmlFor>` (auth/invite) or a
  `VisuallyHidden`/`aria-label` where space-constrained (the diagnostic typed answer already uses
  both a `.visually-hidden` span **and** `aria-label` - pick one to avoid double-labelling; prefer
  the visible-hidden `<label>`).
- Errors: associate via `aria-describedby` and set `aria-invalid` (centralised in `TextField`).
- Keep native constraints (`required`, `type="email"`, `minLength={8}`, `autoComplete`) - they
  give browser-level validation and a11y for free (already present in `LoginPage`/`RegisterPage`).

### 3.9 Target sizes (WCAG 2.5.5 AAA / 2.5.8 AA)

- Interactive targets ≥ **44×44** CSS px (palette cells, A–E rows, Flag/Submit, list links on
  touch). The palette uses `aspect-ratio: 1` cells - ensure the computed min size on mobile is
  ≥44px (set a `min-width`/`min-height`). §4.2 enforces this on the runner.

### 3.10 Headings & landmarks (WCAG 1.3.1, 2.4.6)

- One `<h1>` per page (runner: contest+year; lists: "Practice tests" etc.); `Question` uses `<h2>`,
  `ExamReview`/`ProgressView` use `<h2>` section headings - preserve order, no skips.
- Landmarks: `<header>`, `<nav aria-label="Primary">`, `<main>` exist; `ProgressView` already uses
  `aria-labelledby` on its `<section>`s - good pattern to keep.

### 3.11 Testing approach

Tooling present: **vitest + @testing-library/react + @testing-library/user-event +
@testing-library/jest-dom + jsdom + msw**, and **`eslint-plugin-jsx-a11y`**. **axe is NOT
installed.**

- **Add** `vitest-axe` (or `jest-axe`) + `axe-core` as devDeps and a `toHaveNoViolations` matcher
  in `src/test/setup.ts`. Per-component smoke test:

  ```ts
  import { axe } from 'vitest-axe'
  it('has no axe violations', async () => {
    const { container } = render(<Question problem={fixture} selected={null} onSelect={vi.fn()} onClear={vi.fn()} />)
    expect(await axe(container)).toHaveNoViolations()
  })
  ```

  (jsdom can't compute real colour contrast, so run an **axe contrast pass in CI against the
  built app** - Playwright + `@axe-core/playwright` on the key routes - to cover 1.4.3 properly.)
- **Behavioural a11y tests** (the gap jsx-a11y/axe can't fill), using `user-event` keyboard APIs:
  - **Palette roving tabindex**: Tab reaches the palette as a single stop; ArrowRight/Left/Up/Down
    move focus; Home/End jump; Enter/Space fires `onSelect`. Extend the existing
    `Palette.test.tsx` (which already asserts
    labels + `aria-current`).
  - **RadioGroup**: Arrow keys change selection; Tab treats the group as one stop; `<fieldset
    disabled>` blocks interaction after submit (assert no `onChange`).
  - **Timer milestones**: advance fake timers (the runner already uses fake-timer-friendly
    `useCountdown`); assert the milestone region's text at 5:00/1:00/0:00 and that auto-submit
    fires exactly once (mirrors `useCountdown.test.ts`).
  - **Focus management**: after submit success, focus lands on the review heading; on route
    change, focus moves to `<main>`.
  - **Form association**: `TextField` renders `aria-invalid`/`aria-describedby` when `error` set;
    `getByRole('alert')` contains the message.
- **Coverage**: keep the project's 80% line / 70% branch gate; runner state + countdown stay at
  the spec's high bar (tech-spec §Testing names runner state, palette nav, self-mark recompute).
- **Manual pass** (the "basic a11y pass" deliverable): keyboard-only walkthrough of the runner
  (take + submit an exam with no mouse), a screen-reader smoke (VoiceOver/NVDA) on the runner and
  progress dashboard, and a reduced-motion + 200% zoom check.

---

## 4. Responsive plan

### 4.1 Breakpoint strategy (tokens)

Today there are **no breakpoint tokens** and **one hardcoded** media query (`@media (min-width:
720px)` for the runner grid in `index.css`). Define a token-documented scale and use it
consistently. CSS custom properties can't be used inside `@media` conditions, so the "tokens" are
**documented named values + (optionally) a Sass/PostCSS map**; the contract is that the same
named breakpoints are used everywhere.

| Name | Min-width | Used for |
|------|-----------|----------|
| `sm` | 480px | small-phone → large-phone tweaks |
| `md` | 768px | tablet; **runner palette becomes sidebar**, progress tables un-stack |
| `lg` | 1024px | desktop; wider content, multi-column dashboards |

- **Mobile-first**: base styles target the smallest screen; `min-width` queries enhance upward
  (matches the existing runner CSS). **Minimum supported viewport: 360px wide** (small modern
  phones); nothing may horizontally scroll at 360px except deliberately scrollable math (§5).
- Migrate the existing `720px` runner query to the `md` (768px) token value during the CSS-Modules
  migration so all breakpoints align.
- **New tokens to add** to `:root` alongside the migration (referenced throughout this doc):
  `--focus-ring` (e.g. `3px solid var(--color-primary)` consolidated from the global rule),
  `--z-overlay` / `--z-toast` (drawer/toast stacking), `--color-info` (Alert info severity), a
  `--motion-fast` duration token (zeroed under reduced-motion). These are additive and low-risk.

### 4.2 Exam runner - the hard screen

Current: `.runner__body` is `grid-template-columns: 1fr` (stacked) and becomes `12rem 1fr` at
720px - palette left, question right. Build on that:

- **Desktop (≥ `md`)**: palette as a **sticky sidebar** (`position: sticky; top: <header-height>`)
  in the left column so it stays visible while the question scrolls; question is the right column,
  **single-column** body. (Already two-column; add `sticky`.)
- **Mobile (< `md`)**: a full sidebar wastes vertical space and pushes the question below the fold.
  Move the palette into a **collapsible drawer / bottom sheet** opened by a "Questions (k/N
  answered)" toggle button pinned near the controls:
  - Toggle is a real `<button aria-expanded aria-controls="palette">`.
  - The drawer is a `role="dialog" aria-modal="true"` panel (labelled "Question navigator") that
    **traps focus, closes on Esc, and restores focus to the toggle** (§3.2). Selecting a question
    closes the drawer and moves focus to the question heading.
  - Honour `prefers-reduced-motion` for the slide-in (§3.7).
- **Single-column question** at all widths (already the case) - the body and A–E stack vertically.
- **Touch sizing** (§3.9): A–E `.choice` rows and the Flag/Submit/Prev/Next controls must be
  ≥44px tall with comfortable spacing on mobile; palette cells `min` 44px. The controls bar
  (`.runner__controls`) already `flex-wrap`s - ensure it doesn't produce sub-44px buttons when it
  wraps.
- **Sticky timer**: keep the timer + answered-count visible while scrolling on mobile (sticky
  header) so the countdown is never scrolled away during an exam.
- **Performance implication** (tech-spec: **exam page interactive < 2 s**, Lighthouse): KaTeX is
  the heavy dependency and is **already** lazy-loaded - the runner route is `React.lazy`-split in
  `App.tsx`, so KaTeX is not in the login/list bundle and only loads
  when the runner mounts. Keep it that way: don't import `Tex`/`katex` into shared chunks (lists,
  layout). The drawer, milestone region, and roving-grid logic are tiny and must not pull KaTeX
  earlier. Consider prefetching the runner chunk on list-item hover/focus to shave first-paint of
  the runner without bloating the catalog bundle.

### 4.3 Progress dashboard - multi-table → stacked cards

Current: `ProgressView` renders the recommendation/algebra-warning section plus **two wide
tables** (contest history: Score/Correct/Wrong/Blank/Time; diagnostics: Instrument/Verdict/Result)
styled by `.progress__table`. Five-column tables overflow at 360px.

- **Desktop (≥ `md`)**: keep the semantic `<table>`s as-is.
- **Mobile (< `md`)**: collapse each table to **stacked cards** - one `Card` per row, each
  field shown as a **label → value** pair. Two acceptable techniques (pick one and standardise in
  `ui/Table`):
  1. **CSS responsive table**: keep the real `<table>` DOM (preserves semantics); at < `md` set
     rows to `display: block`, hide the `<thead>` visually, and surface each `<td>`'s header via
     `data-label` + `::before` content. Header→value association is retained for AT.
  2. **Definition-list cards**: render a `<dl>` per row at mobile widths with explicit `<dt>`/`<dd>`.
  - Either way: **no horizontal scroll** at 360px, and the header text remains available to screen
    readers (don't just drop the `<thead>`). (WCAG 1.3.1, 1.4.10 reflow.)
- The recommendation + **algebra-gate `Alert`** sit full-width above the tables at all sizes.
- **Reflow (WCAG 1.4.10)**: the whole app must be usable at **320px equivalent / 400% zoom**
  without 2-D scrolling - the dashboard stack and the runner drawer are what make this pass.

### 4.4 Lists, forms, header

- **List pages** (`ExamListPage`, `DiagnosticListPage`): single-column stacked links/`Card`s
  already (`display: grid; gap`); ensure tap targets ≥44px. The contest filter bar
  (`.filter-bar`) should wrap, not overflow, on narrow screens.
- **Auth/invite forms**: already constrained (`max-width: 28rem`, single column) - fine; just
  route them through `TextField`/`Select`.
- **Header** (`.layout__header`): already `flex-wrap`s with the user block pushed `margin-left:
  auto`; on the narrowest widths verify the nav wraps to a usable two-row layout (or introduce a
  menu only if it actually crowds - not required now).

---

## 5. Math rendering (KaTeX) - a11y + responsive

Grounded in `components/Tex.tsx`: a memoized `<Tex>` that
calls `katex.renderToString(tex, { displayMode, throwOnError: false, output: 'htmlAndMathml' })`
and injects the result once via `dangerouslySetInnerHTML` into a `<span data-testid="math">`.
KaTeX CSS is imported once in `main.tsx`. Used by `Question` (problem body + choices) and the
diagnostic prompts.

### 5.1 Screen-reader accessibility (MathML)

- `output: 'htmlAndMathml'` already emits **two** trees: the visual HTML (KaTeX spans) **and** an
  MathML tree (`<math>…`). KaTeX marks its visual layer `aria-hidden="true"` and exposes the
  MathML to AT - so a screen reader reads the equation **once** (from MathML), not the visual
  spans. **Keep `htmlAndMathml`** (don't switch to `html`-only, which would leave AT with nothing,
  or `mathml`-only, which drops the styled visual). MathML AT support is good in
  VoiceOver/Orca/JAWS; this is the correct accessible default and requires no extra wrapper ARIA.
- **Do not add a conflicting role/label** to our wrapping `<span data-testid="math">` - let
  KaTeX's own MathML/`aria-hidden` split stand. If a problem ever needs a human-authored verbal
  description, prefer real MathML/`alt`-style text over an `aria-label` guess.
- **`throwOnError: false`** is an a11y win too: malformed TeX renders a visible error string
  instead of crashing mid-exam (the `#CRITICAL` note in `Tex.tsx`) - keep it.
- Image-mode problems are **not** KaTeX - they rely on the `<img alt="Problem N">` in `Question`
  (§1.5). That's the correct fallback for scanned problems.

### 5.2 Responsive / overflow (don't let equations break layout)

This is the main **add** for math on mobile. Display equations (`displayMode`, problem bodies) can
be **wider than a 360px viewport** and would otherwise force the whole page to horizontally scroll
or get clipped.

- Wrap display math in a container that **scrolls horizontally on overflow, scoped to the
  equation** - `overflow-x: auto` on the math container (in `Tex`'s display branch or a wrapping
  element in `Question.__body`), with `max-width: 100%`. The page never side-scrolls; only the
  over-wide equation does, inside its own box. (KaTeX renders fixed-layout HTML, so a wrapping
  scroll container is the standard fix.)
- Give the scroll container a visible affordance (subtle edge fade or a thin scrollbar) and make
  it **keyboard-scrollable / focusable** (`tabIndex={0}` + an `aria-label` like "scrollable
  equation") so keyboard users can pan a very wide equation - but keep this off the MathML so it
  isn't double-announced.
- **Inline math** (choice bodies, in-prompt math) should wrap with surrounding text where possible
  and not blow out the line; constrain choice rows so an over-wide inline expression scrolls within
  the `.choice__body`, not the page.
- Respect zoom/reflow (1.4.10): at 400% zoom equations must remain readable via the scroll
  container rather than clipping.
- **Performance**: the memo in `Tex` (one `renderToString` per `[tex, display]`) already avoids
  re-rendering KaTeX on unrelated re-renders - important on the runner where parent state changes
  every second (the timer tick) but the problem TeX doesn't. Keep the memo; keep KaTeX
  route-lazy-loaded (§4.2) so it never threatens the exam-interactive-<2s budget.

### 5.3 Tests for math

- Existing tests assert the rendered math node (`data-testid="math"`); add a check that **MathML is
  present** in `Tex` output (assert a `<math>` element exists) so a future `output` regression is
  caught, and an axe smoke on a `Question` with display math.

---

## 6. Implementation order (suggested, Phase-3-aligned)

1. **Tokens & shell**: add the new tokens (focus-ring, z, info, motion) and the **skip link** +
   **route-change focus** in `Layout`; start the `index.css` → tokens-only diet.
2. **Primitives**: `Button`, `TextField`, `Select`, `Checkbox`, `Alert`, `Badge`, `Card`, the
   `cx` helper, and the `ui/` barrel - each module-first; migrate auth/invite/list pages onto them.
3. **Extract `RadioGroup`** from `Question`; **refactor `Palette` to roving tabindex**; add the
   `Timer` chip + **milestone live region**. Update `Palette.test.tsx` + add RadioGroup/keyboard
   tests.
4. **Responsive**: runner palette **drawer** on mobile + sticky sidebar/timer on desktop;
   `Table` responsive **stacked-card** behaviour for the progress dashboard; verify 360px / 400%.
5. **Math**: equation **overflow scroll** containers; MathML presence test.
6. **A11y harness**: add `vitest-axe` + per-component axe smokes; add `@axe-core/playwright`
   contrast/route pass in CI; run the manual keyboard + screen-reader + reduced-motion pass.

Each of these is a feature/refactor branch per the project's branch-workflow rule (`feat/…` /
`refactor/…`), not committed to `main` directly.
