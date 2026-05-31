# AMC Trainer — Frontend Design Plan

The design plan for the AMC Trainer frontend, produced as a set of
implementation-ready specs. This index ties them together, records the locked
decisions, and consolidates the cross-cutting findings and follow-ups the specs
surfaced.

## Locked decisions

| Decision | Value |
|----------|-------|
| Styling foundation | **CSS Modules + design tokens** (CSS custom properties). No Tailwind, no UI component library. |
| Visual tone | **Clean & academic** — calm, focused, exam-serious, high legibility for math. |
| First pass scope | Design docs **plus a coded prototype** (tokens extracted + key screens converted). |
| Auth (v1) | Built-in invite + password + server-side sessions (Authentik SSO is a documented future option). |

## The documents

| Doc | What it covers | Read it when |
|-----|----------------|--------------|
| [design-system.md](design-system.md) | Canonical token spec: color (light + dark contract, WCAG AA verified), typography (system stack + scale, KaTeX legibility), spacing/radius/shadow/z/breakpoints, naming, theming, motion. Ships a copy-paste `tokens.css`. | Building any styling. The source of truth. |
| [ux-flows.md](ux-flows.md) | Information architecture, role-aware navigation, the three core journeys (US-001/002/003) + coach flow, ASCII wireframes for every screen (desktop + mobile), states, microcopy, 11 open UX questions. | Designing or building any screen. |
| [component-library.md](component-library.md) | Component inventory (keep/refactor/add), CSS-Modules composition + file layout, the accessibility plan (keyboard model, aria-live, WCAG mapping, test approach), the responsive plan, KaTeX a11y. | Building shared components / a11y / responsive. |
| [exam-runner-ux.md](exam-runner-ux.md) | Deep dive on the timed test: timer behavior + urgency tiers, answering + full keyboard model, submit / auto-submit / double-submit / 409, the review screen, edge cases, prioritized improvements. | Working on the runner (the centerpiece). |

Read order for a newcomer: **design-system → ux-flows → component-library →
exam-runner-ux**.

## How the pieces fit

```text
design-system.md  ──► tokens.css ──► every component's *.module.css
        │
ux-flows.md  ──────► what each screen is + its states/copy
        │
component-library.md ─► the shared components those screens compose, + a11y/responsive rules
        │
exam-runner-ux.md ───► the hardest screen, specified to the keystroke
```

All four are written against the **real codebase** (the existing
`frontend/src/` pages, features, and `index.css` tokens) and the committed
**OpenAPI shapes** (`docs/api/openapi.json`) — so they refine what exists rather
than describe a greenfield app. The styling specs evolve the current
`index.css` token *names* rather than rewriting them.

## Cross-cutting findings to act on

The specs independently surfaced a few items that matter beyond styling. Captured
here so they aren't lost in 3,400 lines of docs:

### Product / UX gaps (from ux-flows + exam-runner-ux)

1. **Refresh resets the timer (integrity + data-loss risk).** The countdown is
   anchored on `Date.now()` at component mount, so a page refresh restarts the
   clock and discards in-progress answers. A student could refresh for free time.
   *Fix direction:* anchor the deadline on a server `started_at` (create the
   attempt on exam open) and persist in-progress answers. **Top-ranked
   recommendation.**
2. **A bare 409 can dead-end the review.** The runner treats the server's 409
   "already submitted" as terminal but has no graded `result` to show, so the
   review can't render. *Fix direction:* have the submit endpoint return the
   existing result on 409.
3. **No confirm-before-submit and no low-time warning** exist today. Add a
   confirm dialog (manual submit, when blanks remain) and 5:00 / 1:00 warnings.
4. **Coach can't reach a student.** `/users/:id/progress` exists but has no UI
   entry point (requires typing a UUID). Needs a staff-only roster + a
   list-students endpoint.
5. **Diagnostic result is under-built** vs. the API: `group_scores` and per-item
   `review[]` are returned but not shown.

### API-contract follow-ups (worth logging in `docs/template_feedback.md` / a tech-spec note)

- The submit endpoint documents only `200`/`422` — no `409` returning the prior
  result (finding #2).
- No `solution_url` / `source_url` is exposed for the review screen, though
  `Exam.source_url` is stored server-side — the "solution link out" the review
  wants needs an API addition.
- `ProgressResponse.test_attempts[]` items are untyped (`{}`) and lack a
  paper label / date for history rows.

### Accessibility baseline (from component-library)

- Exam runner: choices as a labelled **radiogroup**, palette as a **roving-tabindex**
  grid, `role="timer"` with **sparse `aria-live` milestones** (not every second),
  focus management on phase/route changes, and **color is never the only signal**.
- Tooling: `eslint-plugin-jsx-a11y` is already wired; add axe smoke tests +
  keyboard-interaction tests.

## Recommended build order (from component-library §6)

1. **Tokens & shell** — extract `tokens.css`; add skip-link + route-change focus.
2. **Primitives** — `Button`, `TextField`, `Select`, `Checkbox`, `Alert`,
   `Badge`, `Card` (+ a `cx` helper), each module-first; migrate the auth/list
   pages onto them.
3. **Runner refinements** — extract `RadioGroup` from `Question`, refactor
   `Palette` to roving tabindex, add the `Timer` chip + milestone live region.
4. **Responsive** — runner palette drawer on mobile; dashboard tables → stacked
   cards.
5. **Math** — equation overflow-scroll containers; MathML presence test.
6. **A11y harness** — axe smokes + manual keyboard/SR/reduced-motion pass.

Each is a `feat/…` or `refactor/…` branch per the project's branch-workflow rule.

## Prototype status

Per the chosen "docs + coded prototype" scope, the first prototype slice landed:

- **Tokens (build step 1):** `frontend/src/styles/tokens.css` extracted verbatim
  from the design-system spec (light + dark contract), imported in `main.tsx`
  before `index.css`. `index.css` trimmed to reset + element defaults + the
  KaTeX/reduced-motion globals; its `:root` token block now lives in
  `tokens.css`. Existing components keep working via the back-compat aliases.
- **A primitive (step 2):** `components/ui/Button.tsx` + `Button.module.css` and
  a 3-line `lib/cx.ts` helper — the props→className + token-consuming pattern.
- **Two converted screens (steps 2–3):** the **Login** page (`LoginPage.module.css`
  + the `Button` primitive) and the runner **Palette** (`Palette.module.css`,
  token-driven answered/flagged/current/voided states) — proving the CSS-Modules
  pattern on both a simple screen and a runner component.

The whole frontend stays green: `tsc -b`, eslint, 15 vitest tests, `vite build`,
prettier, and the API-client drift check all pass.

The remaining build-order steps (more primitives, the RadioGroup extraction,
roving-tabindex palette, responsive drawer, a11y harness) are tracked above and
left as `feat/…` / `refactor/…` follow-ups.
