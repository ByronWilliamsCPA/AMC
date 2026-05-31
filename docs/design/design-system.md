# AMC Trainer — Design System & Token Specification

> **Status**: Canonical · **Version**: 1.0 · **Updated**: 2026-05-31
> **Scope**: This is the source-of-truth design-system and design-token spec for the AMC
> Trainer frontend. All other frontend docs and the implementation build on it. An engineer
> should be able to write `tokens.css` directly from §2–§4 and §5.

## 0. Context & locked decisions

AMC Trainer is a web app where a math coach and up to ~30 students take **timed AMC 8/10/12
practice contests** and **AoPS placement diagnostics**, then get a synthesized course
recommendation. The exam runner is the highest-stakes surface: a student is under a countdown,
reading math, and one misread choice changes their score.

These decisions are **locked**; this doc designs within them, it does not relitigate them.

| Decision | Value |
|----------|-------|
| Styling foundation | **CSS Modules + design tokens as CSS custom properties**. No Tailwind, no UI component library. |
| Dependencies | Minimal-dependency ethos. The only styling-adjacent runtime dep is **KaTeX** (`katex` `^0.16`), already used by `frontend/src/components/Tex.tsx`. **No web fonts.** |
| Visual tone | **Clean & academic** — calm, focused, exam-serious, high legibility for math, restrained single accent, minimal chrome. |
| Target stack | React 19 + TypeScript 5.7 + Vite 6 (already set up). |
| Performance budget | Exam page interactive **< 2 s** (`tech-spec.md` §Performance). System fonts + CSS vars keep CSS cost near-zero; this is a hard constraint on the design. |

**Relationship to existing code.** `frontend/src/index.css` already defines a starter token set
(`--color-bg`, `--color-fg`, `--color-muted`, `--color-primary`, `--color-primary-fg`,
`--color-border`, `--color-ok`, `--color-warn`, `--color-error`, `--color-surface`,
`--space-1..5`, `--radius`, `--maxw`, `--font`). This spec is an **evolution, not a rewrite**:
every existing name is preserved (some as the canonical token, some as a back-compat alias), and
the existing hex values are kept wherever they already pass WCAG AA — which, after verification,
is all of them. New tokens are additive.

---

## 1. Design principles

Six principles, ordered. When two conflict, the lower number wins.

1. **Legibility before everything.** Students read dense math under time pressure. Body text is
   ≥ 16px with generous line-height; math (KaTeX) is sized to sit at or slightly above the prose
   x-height so fractions and exponents stay readable; numerals are tabular where they're compared
   (timer, scores, problem palette). Never trade contrast or size for prettiness.

2. **Low distraction during a timed test.** The runner is near-monochrome: one restrained
   accent, lots of calm surface, no gradients, no decorative motion, no animated timers. Color is
   spent only where it carries meaning (current question, flagged, answered, correct/incorrect in
   review). Chrome recedes so the problem is the only loud thing on screen.

3. **Trustworthy & serious.** This is exam software; it should feel like a proctored test, not a
   gamified quiz app. Restrained academic blue accent, square-ish geometry (small radii), flat
   surfaces with hairline borders rather than heavy shadows. No emoji, no playful illustration, no
   celebratory confetti. State changes are immediate and unambiguous.

4. **Accessible by default, not as a retrofit.** Every text/background pair in this doc meets
   **WCAG 2.1 AA** (4.5:1 body, 3:1 large/UI) — verified, see §2. Meaning is **never carried by
   color alone**: answered/flagged/correct/incorrect/voided each pair color with a glyph, label,
   border, or text change. Visible keyboard focus everywhere (already in `index.css`). Touch
   targets ≥ 44px. Respect `prefers-reduced-motion` and `prefers-color-scheme`.

5. **Consistent through tokens.** No raw hex, px font sizes, or magic spacing in component CSS.
   Components consume tokens (`var(--color-*)`, `var(--space-*)`, …) only. This is what makes the
   light→dark contract (§6) and any future re-theme a config change, not a refactor.

6. **Responsive for "whatever device is handy."** Students practice on laptops and tablets
   (`project-vision.md`). The runner is single-column on small screens and grows a question-palette
   sidebar at ≥ 720px (the existing `--bp-md` breakpoint). Layout is fluid; the type scale does not
   shrink below the legibility floor on small screens.

---

## 2. Color tokens

### 2.1 Approach

- **Neutrals** are a cool, very-slightly-blue gray ramp (not pure gray) so the academic-blue
  accent feels native rather than bolted on. Two text weights (primary, muted) plus a third
  "subtle" for de-emphasized metadata; three surface levels; two border weights.
- **One accent**: an academic blue (`--color-primary` `#2d4ea2`, kept from the existing file). A
  darker `-strong` step for hover/active, a `-soft` tint for selected backgrounds.
- **Semantic colors**: success/correct, warning, error/incorrect, info, and **voided/muted**
  (the AMC "this problem doesn't count" state). Each has a **text-weight** value (readable on the
  page background), a **soft** tinted surface, and an **fg-on-soft** value for text inside a tinted
  chip. This three-part shape is what review tables and the palette need.

### 2.2 Contrast intent (verified)

All pairs below were computed with the WCAG relative-luminance formula. **Intent column = the bar
the pair must clear.** All listed pairs **PASS**.

| Pair (light) | Ratio | Intent |
|---|---|---|
| `--color-text` `#1a1a2e` on `--color-bg` `#ffffff` | 17.06 | body 4.5:1 — primary reading text |
| `--color-text` on `--color-surface` `#f4f6fb` | 15.78 | body 4.5:1 — text on cards/panels |
| `--color-text` on `--color-surface-raised` `#eceff6` | 14.82 | body 4.5:1 — text on raised rows |
| `--color-text-muted` `#54546b` on `#ffffff` | 7.35 | body 4.5:1 — secondary text |
| `--color-text-muted` on `--color-surface` | 6.80 | body 4.5:1 — secondary text on panels |
| `--color-text-subtle` `#6b6b85` on `#ffffff` | 5.16 | body 4.5:1 — metadata, hints |
| `--color-primary` `#2d4ea2` on `#ffffff` | 7.71 | body 4.5:1 — links, accent text |
| `--color-primary-strong` `#274690` on `#ffffff` | 8.88 | body 4.5:1 — hover/active accent text |
| `--color-on-primary` `#ffffff` on `--color-primary` | 7.71 | body 4.5:1 — button label |
| `--color-success-text` `#16703f` on `#ffffff` | 6.13 | body 4.5:1 — "correct" text |
| `--color-success-text` on `--color-success-soft` `#e3f3e9` | 5.33 | body 4.5:1 — text in correct chip |
| `--color-warning-text` `#8a4f00` on `#ffffff` | 6.56 | body 4.5:1 — "flagged"/caution text |
| `--color-warning-text` on `--color-warning-soft` `#fbeed9` | 5.73 | body 4.5:1 — text in caution chip |
| `--color-error-text` `#b00020` on `#ffffff` | 7.33 | body 4.5:1 — "incorrect" text |
| `--color-error-text` on `--color-error-soft` `#fbe4e7` | 6.05 | body 4.5:1 — text in incorrect chip |
| `--color-info-text` `#1f5fa8` on `#ffffff` | 6.44 | body 4.5:1 — info/notice text |
| `--color-info-text` on `--color-info-soft` `#e4eefb` | 5.50 | body 4.5:1 — text in info chip |
| `--color-voided-text` `#6b6b85` on `#ffffff` | 5.16 | body 4.5:1 — voided "doesn't count" text |
| `--color-text` on any `*-soft` tint (success/warn/error/info/primary) | 14.1–14.9 | body 4.5:1 — body text on tinted rows |
| `--color-focus` `#2d4ea2` ring on `#ffffff` | 7.71 | UI 3:1 — focus indicator |

> **Borders are intentionally below 3:1.** `--color-border` `#d4d7e0` (1.44:1 on white) and
> `--color-border-strong` `#b9bdcb` (1.87:1) are **decorative separators**, not the sole signal of
> any state or control boundary. Per Principle 4, every interactive/stateful element also carries a
> text label, glyph, fill, or focus ring — so the borders are not load-bearing for WCAG 1.4.11.

Dark-theme pairs were verified identically (text on bg 15.14, muted 7.97, every semantic
text-on-bg 7.7–9.0, every `fg-on-soft` 9.4–9.9). The dark ramp is defined in §2.4.

### 2.3 Light theme tokens (the default `:root`)

```css
/* ---- Neutrals: cool gray ramp ---- */
--color-bg:              #ffffff; /* app background / page */
--color-surface:         #f4f6fb; /* cards, panels, list rows  (was #f5f6fa) */
--color-surface-raised:  #eceff6; /* hovered/selected rows, sticky bars */
--color-surface-sunken:  #e4e7f0; /* wells, code blocks, inset areas */
--color-border:          #d4d7e0; /* hairline separators (decorative) */
--color-border-strong:   #b9bdcb; /* emphasized dividers, input borders on focus-within */
--color-text:            #1a1a2e; /* primary reading text */
--color-text-muted:      #54546b; /* secondary text, captions   (was --color-muted #5b5b73) */
--color-text-subtle:     #6b6b85; /* de-emphasized metadata, placeholders */
--color-text-inverse:    #ffffff; /* text on dark/accent fills */

/* ---- Accent (academic blue) ---- */
--color-primary:         #2d4ea2; /* kept from existing file */
--color-primary-strong:  #274690; /* hover / active / pressed */
--color-primary-soft:    #e6ecf8; /* selected background tint */
--color-on-primary:      #ffffff; /* text/icon on a primary fill (was --color-primary-fg) */

/* ---- Semantic: correct ---- */
--color-success:         #1b7f4b; /* solid fill / icon (was --color-ok) */
--color-success-text:    #16703f; /* "correct" text on bg */
--color-success-soft:    #e3f3e9; /* correct row / answered-cell tint */

/* ---- Semantic: warning / flagged / caution ---- */
--color-warning:         #9a5b00; /* solid fill / flag icon (was --color-warn) */
--color-warning-text:    #8a4f00; /* caution text on bg */
--color-warning-soft:    #fbeed9; /* flagged tint */

/* ---- Semantic: incorrect / error ---- */
--color-error:           #b00020; /* solid fill / icon (kept) */
--color-error-text:      #b00020; /* "incorrect" text on bg */
--color-error-soft:      #fbe4e7; /* incorrect row tint */

/* ---- Semantic: info / notice ---- */
--color-info:            #1f5fa8;
--color-info-text:       #1f5fa8;
--color-info-soft:       #e4eefb;

/* ---- Semantic: voided / muted ("does not count") ---- */
--color-voided-text:     #6b6b85; /* voided problem label */
--color-voided-soft:     #eef0f4; /* voided row/cell tint (paired with line-through) */

/* ---- Functional aliases ---- */
--color-focus:           var(--color-primary); /* focus ring colour */
--color-link:            var(--color-primary);
--color-overlay:         rgb(18 19 26 / 0.45); /* modal/scrim backdrop */

/* ---- Back-compat aliases (existing index.css names → canonical) ---- */
--color-fg:              var(--color-text);
--color-muted:           var(--color-text-muted);
--color-primary-fg:      var(--color-on-primary);
--color-ok:              var(--color-success);
--color-warn:            var(--color-warning);
```

> Keeping `--color-fg`, `--color-muted`, `--color-primary-fg`, `--color-ok`, `--color-warn` as
> aliases means the current `index.css` rules keep working unchanged while components migrate to the
> canonical names at their own pace.

### 2.4 Dark theme tokens (the contract, ships later)

Dark mode is a **named-token contract defined now**; it may ship in a later phase, but the contract
is fixed so no component hardcodes a light-only value. It is applied via `[data-theme="dark"]`
(see §6). Only the values that change are overridden — the structural tokens (spacing, radius, type,
z-index) are theme-independent.

```css
[data-theme="dark"] {
  /* Neutrals */
  --color-bg:             #12131a;
  --color-surface:        #1a1c26;
  --color-surface-raised: #232634;
  --color-surface-sunken: #0e0f16;
  --color-border:         #3a3d4d;
  --color-border-strong:  #4c4f63;
  --color-text:           #e6e8f0;
  --color-text-muted:     #a6a9bd;
  --color-text-subtle:    #8d90a6;
  --color-text-inverse:   #12131a;

  /* Accent — lightened so it reads on a dark bg (text on bg ≥ 8.6:1) */
  --color-primary:        #8fb0ff;
  --color-primary-strong: #aec4ff;
  --color-primary-soft:   #17223d;
  --color-on-primary:     #0e0f16;

  /* Semantic: lightened text/icon, deep tinted surfaces */
  --color-success:        #5cc98c;
  --color-success-text:   #9fe0bb;
  --color-success-soft:   #15301d;

  --color-warning:        #e0a44d;
  --color-warning-text:   #f0c98a;
  --color-warning-soft:   #2e2410;

  --color-error:          #f2899a;
  --color-error-text:     #f6b3bf;
  --color-error-soft:     #2e1419;

  --color-info:           #7db0ec;
  --color-info-text:      #aaccf5;
  --color-info-soft:      #13243a;

  --color-voided-text:    #8d90a6;
  --color-voided-soft:    #1f2230;

  /* Functional */
  --color-overlay:        rgb(0 0 0 / 0.6);
  /* aliases inherit automatically via var() indirection */
}
```

> **KaTeX in dark mode.** KaTeX renders math as glyphs that inherit `color`, so math follows
> `--color-text` for free. The one risk is KaTeX's `\rule`-based fraction bars and matrix lines,
> which also use `currentColor` and are therefore fine. Problem **images** (`render_mode == "image"`,
> see `tech-spec.md` Problem model) are raster PNGs with white backgrounds and will *not* invert; in
> dark mode they must be wrapped in a token-driven light "paper" frame (`--color-image-mat`,
> defined as `#ffffff` in both themes) so scanned problems stay legible. Noted here so the dark
> rollout doesn't regress image problems.

---

## 3. Typography tokens

### 3.1 Font stacks (no web-font dependency)

A web font would add a render-blocking download and fight the **< 2 s interactive** budget, so we
use the system UI stack already in `index.css`. The justification bar for ever adding a web font:
only if a metric demands it (it does not today).

```css
--font-sans: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue',
             Arial, 'Noto Sans', sans-serif;            /* was --font */
--font-mono: ui-monospace, 'SF Mono', 'Source Code Pro', Menlo, Monaco,
             Consolas, 'Courier New', monospace;        /* code, raw answers */
--font-math: 'KaTeX_Main', 'Latin Modern Math', serif;  /* documentary only — KaTeX sets its own */
--font: var(--font-sans);                               /* back-compat alias */
```

- **Prose & UI**: `--font-sans`. Sans-serif maximizes on-screen legibility at small sizes.
- **Math**: KaTeX ships and applies its own `KaTeX_*` font faces via the CSS imported in
  `main.tsx` (`katex/dist/katex.min.css`). We do **not** restyle KaTeX glyph fonts; `--font-math`
  exists only to document the rendered family. See §3.5.
- **Mono**: raw student answers in diagnostics (`5/7`, `2^7`), code-like content, and the invite
  token. Tabular by nature.

### 3.2 Type scale (modular, ~1.2 minor-third, rounded to clean px)

Sizes are tokens in `rem` (root = 16px). Each size pairs with a default line-height token. The
scale floor for body is **1rem/16px** — the legibility floor from Principle 1; nothing in reading
content goes below it.

```css
--font-size-xs:   0.75rem;  /* 12px — table captions, fine print, dt labels */
--font-size-sm:   0.875rem; /* 14px — secondary UI, metadata */
--font-size-base: 1rem;     /* 16px — body, problem prose, choices (floor) */
--font-size-md:   1.125rem; /* 18px — emphasized body, lead-in */
--font-size-lg:   1.25rem;  /* 20px — section headings, score figures */
--font-size-xl:   1.5rem;   /* 24px — page titles, the runner timer */
--font-size-2xl:  1.875rem; /* 30px — dashboard headline numbers */
--font-size-3xl:  2.25rem;  /* 36px — rare hero / verdict screens */

/* Line-heights (unitless) */
--line-height-tight:   1.2;  /* headings, the timer, large numerals */
--line-height-snug:    1.35; /* choices, dense rows, palette labels */
--line-height-normal:  1.6;  /* body & problem prose — roomy for mixed math + text */
--line-height-relaxed: 1.75; /* long solution explanations */

/* Weights — system fonts: 400/600/700 only (avoid faux/odd weights) */
--font-weight-regular:  400;
--font-weight-medium:   600; /* choice letters, emphasized labels, buttons */
--font-weight-bold:     700; /* headings, timer, score figures */

/* Letter-spacing — minimal; only tighten large display, open up all-caps eyebrows */
--letter-spacing-tight: -0.01em; /* 2xl/3xl display numerals */
--letter-spacing-caps:   0.04em; /* small all-caps labels, if used */

/* Numerals — compare-by-column surfaces */
--font-numeric-tabular: tabular-nums; /* timer, scores, palette, tables */
```

### 3.3 Recommended role → token map

| Role | size | line-height | weight |
|------|------|-------------|--------|
| Problem prose / choices | `--font-size-base` | `--line-height-normal` | regular |
| Choice letter (A–E) | `--font-size-base` | `--line-height-snug` | medium |
| Runner timer | `--font-size-xl` | `--line-height-tight` | bold + `tabular-nums` |
| Page title | `--font-size-xl` | `--line-height-tight` | bold |
| Section heading | `--font-size-lg` | `--line-height-tight` | bold |
| Score figure (review/progress `dd`) | `--font-size-lg` | `--line-height-tight` | bold + `tabular-nums` |
| Metadata / `dt` label | `--font-size-xs`–`sm` | `--line-height-snug` | regular, `--color-text-muted` |
| Solution explanation | `--font-size-base` | `--line-height-relaxed` | regular |

### 3.4 Base element defaults

```css
html { font-size: 100%; }                 /* respect user's browser font-size */
body {
  font-family: var(--font-sans);
  font-size: var(--font-size-base);
  line-height: var(--line-height-normal);
  color: var(--color-text);
  background: var(--color-bg);
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}
```

### 3.5 Rendering math (KaTeX) legibly alongside prose — explicit guidance

`Tex.tsx` calls `katex.renderToString(..., { output: 'htmlAndMathml' })` and injects the result;
KaTeX styling comes from the imported `katex.min.css`. Rules for keeping math legible **without
forking KaTeX's CSS**:

1. **Inline math must not shrink.** Inline KaTeX inherits the surrounding `font-size`. Set problem
   prose to `--font-size-base` (16px floor) so inline fractions/exponents render at a readable size.
   Never place math inside `--font-size-xs`/`sm` text.

2. **Nudge math optical size up ~4–6%.** KaTeX's x-height runs slightly small against system sans.
   Apply a single token-driven bump to rendered math so symbols match prose weight:

   ```css
   .katex { font-size: var(--math-scale); }   /* --math-scale: 1.05; */
   ```

   Keep it global and small; do **not** per-component override (Principle 5). `--math-scale` is a
   typography token (see §3.6).

3. **Display equations get vertical breathing room, centered.** `displayMode` math (block) needs
   space so numerators/denominators don't crowd the lines above/below:

   ```css
   .katex-display { margin: var(--space-3) 0; overflow-x: auto; overflow-y: hidden; }
   ```

   `overflow-x: auto` prevents a wide matrix from forcing the whole runner to scroll on a tablet.

4. **Color comes free.** KaTeX glyphs use `currentColor`; they inherit `--color-text`, so dark mode
   and "voided/incorrect" text recoloring apply to math automatically. Don't set explicit colors on
   `.katex`.

5. **Never let bad TeX break layout.** `Tex.tsx` already uses `throwOnError: false`, which renders
   malformed source as KaTeX's error string. Style `.katex-error` with `--color-error-text` so a
   bad problem is visibly flagged, not silently mis-rendered, mid-exam.

6. **Numerals in math vs. UI.** KaTeX numerals are math-set (proportional, which is correct for
   equations). UI numerals that get *compared* (timer, palette, scores) use `--font-numeric-tabular`
   on the **surrounding element**, never on `.katex`.

### 3.6 Math token

```css
--math-scale: 1.05;     /* optical bump applied to .katex (§3.5.2) */
--color-image-mat: #ffffff; /* white "paper" frame behind raster problem images (both themes) */
```

---

## 4. Spacing, radius, shadow, z-index, breakpoints

### 4.1 Spacing scale

The existing `--space-1..5` ramp is kept exactly and **extended** (the runner already relies on its
values). Base unit 4px; the ramp is intentionally not a strict geometric series — it matches what's
already in use, then adds larger steps for page-level rhythm.

```css
--space-0:  0;
--space-1:  0.25rem; /* 4px  — kept */
--space-2:  0.5rem;  /* 8px  — kept */
--space-3:  1rem;    /* 16px — kept (default gap) */
--space-4:  1.5rem;  /* 24px — kept */
--space-5:  2rem;    /* 32px — kept */
--space-6:  3rem;    /* 48px — section separation */
--space-7:  4rem;    /* 64px — page-level vertical rhythm */
```

> **Touch targets (Principle 4):** choices, palette cells, and buttons must render ≥ 44px tall.
> With `--space-2` padding + 16px text + borders, choices clear this; palette cells use
> `aspect-ratio: 1` on a grid whose column width keeps them ≥ 44px on the smallest supported width.

### 4.2 Radius scale

Small radii reinforce the serious/academic tone (Principle 3). Existing `--radius` (6px) is kept and
aliased to the new mid step.

```css
--radius-none: 0;
--radius-sm:   4px;  /* inputs, choice cells, palette cells */
--radius-md:   6px;  /* buttons, cards (kept value) */
--radius-lg:   10px; /* modals, large panels */
--radius-pill: 999px;/* status chips / badges only */
--radius: var(--radius-md); /* back-compat alias */
```

### 4.3 Shadow scale

Flat-first: surfaces are defined by borders, not elevation. Shadows are reserved for genuinely
floating layers (menus, modals, the sticky timer bar when it detaches on scroll). No shadow on
resting cards. Shadows are theme-aware (softer/darker in dark mode via the overlay token approach).

```css
--shadow-none: none;
--shadow-sm:  0 1px 2px rgb(18 19 26 / 0.06);                          /* sticky bars, raised rows */
--shadow-md:  0 2px 8px rgb(18 19 26 / 0.10);                          /* dropdowns, popovers */
--shadow-lg:  0 8px 28px rgb(18 19 26 / 0.16);                         /* modals, dialogs */
--shadow-focus: 0 0 0 3px var(--color-primary-soft);                   /* optional soft focus halo */
```

```css
[data-theme="dark"] {
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.5);
  --shadow-md: 0 2px 8px rgb(0 0 0 / 0.55);
  --shadow-lg: 0 8px 28px rgb(0 0 0 / 0.65);
}
```

### 4.4 Z-index scale

Named layers so stacking is intentional, not a px arms race. The **sticky runner timer** must stay
above scrolling content but below modals/toasts (a student should always see the countdown).

```css
--z-base:     0;
--z-sticky:   100;  /* sticky runner header / timer bar */
--z-dropdown: 200;  /* selects, palette overflow menus */
--z-overlay:  300;  /* modal scrim */
--z-modal:    310;  /* dialog (submit-confirm, session-expiry) */
--z-toast:    400;  /* transient notices, never blocks the timer */
```

### 4.5 Breakpoints

Mobile-first, min-width. `--bp-md` 720px is **kept** — it's the existing runner breakpoint where the
question palette becomes a sidebar (`@media (min-width: 720px)` in `index.css`). Max content width
`--maxw` is kept.

```css
--bp-sm:  480px;  /* large phone */
--bp-md:  720px;  /* tablet — runner palette sidebar appears (kept) */
--bp-lg:  960px;  /* small laptop — matches --maxw content width */
--bp-xl:  1280px; /* large laptop / desktop */
--maxw:   960px;  /* kept — main content max width */
```

> **Note:** CSS custom properties cannot be used inside `@media (min-width: …)` queries. The
> breakpoint *tokens* document the contract and are the single source of truth; in `@media` rules
> write the literal value with a comment, e.g. `@media (min-width: 720px) /* --bp-md */`. (A
> Sass/PostCSS layer is explicitly out of scope per the minimal-dependency ethos.)

---

## 5. Token naming & file layout

### 5.1 Where tokens live

Tokens are CSS custom properties on `:root`, in a dedicated **`frontend/src/styles/tokens.css`**,
imported once at app entry **before** `index.css`:

```
frontend/src/
├── main.tsx                 # imports katex CSS, then tokens.css, then index.css
├── styles/
│   └── tokens.css           # :root tokens + [data-theme="dark"] overrides (THIS SPEC)
├── index.css                # global resets + element defaults + a few global classes
│                            #   (migrate component-specific rules out into *.module.css)
└── features/<x>/<X>.module.css   # component-scoped styles, consume tokens only
```

Import order in `main.tsx` (extends the existing imports):

```ts
import 'katex/dist/katex.min.css'
import './styles/tokens.css'   // tokens first — everything below references them
import './index.css'           // resets + element defaults
```

> `index.css` keeps the global reset, base element styles, focus-visible rule, and `.visually-hidden`
> helper. Component-specific blocks currently in `index.css` (`.runner__*`, `.palette__*`, `.choice*`,
> `.review__*`, …) are migrated into co-located `*.module.css` files over time. The tokens move is the
> prerequisite; this spec does not require a big-bang CSS rewrite.

### 5.2 Naming convention

`--<category>-<role>[-<variant>][-<state>]`, lowercase, hyphen-separated.

| Category prefix | Examples |
|---|---|
| `--color-*` | `--color-bg`, `--color-text-muted`, `--color-primary-strong`, `--color-error-soft` |
| `--space-*` | `--space-1` … `--space-7` |
| `--font-*` / `--font-size-*` / `--font-weight-*` | `--font-sans`, `--font-size-lg`, `--font-weight-bold` |
| `--line-height-*` | `--line-height-normal` |
| `--letter-spacing-*` | `--letter-spacing-tight` |
| `--radius-*` | `--radius-sm`, `--radius-pill` |
| `--shadow-*` | `--shadow-md`, `--shadow-focus` |
| `--z-*` | `--z-sticky`, `--z-modal` |
| `--bp-*` | `--bp-md` (documentary; see §4.5 note) |
| `--math-scale`, `--color-image-mat` | math-specific |

Rules:
- **Semantic over raw.** Components reference role tokens (`--color-error-text`), never a raw palette
  step. There is deliberately no `--blue-500`-style raw layer — at this scale it adds indirection
  without payoff.
- **Soft / strong / text triad** for every semantic colour: `*-text` (readable on bg), `*-soft`
  (tinted surface), solid base (fills/icons). This is the contract review tables & the palette use.
- **Back-compat aliases** keep the original five `index.css` names alive (`--color-fg`,
  `--color-muted`, `--color-primary-fg`, `--color-ok`, `--color-warn`).

### 5.3 `tokens.css` excerpt (authoritative starting point)

```css
/* frontend/src/styles/tokens.css
   Design tokens — single source of truth (see docs/design/design-system.md). */
:root {
  /* ---------- Color: neutrals ---------- */
  --color-bg:             #ffffff;
  --color-surface:        #f4f6fb;
  --color-surface-raised: #eceff6;
  --color-surface-sunken: #e4e7f0;
  --color-border:         #d4d7e0;
  --color-border-strong:  #b9bdcb;
  --color-text:           #1a1a2e;
  --color-text-muted:     #54546b;
  --color-text-subtle:    #6b6b85;
  --color-text-inverse:   #ffffff;

  /* ---------- Color: accent ---------- */
  --color-primary:        #2d4ea2;
  --color-primary-strong: #274690;
  --color-primary-soft:   #e6ecf8;
  --color-on-primary:     #ffffff;

  /* ---------- Color: semantic ---------- */
  --color-success:        #1b7f4b;
  --color-success-text:   #16703f;
  --color-success-soft:   #e3f3e9;
  --color-warning:        #9a5b00;
  --color-warning-text:   #8a4f00;
  --color-warning-soft:   #fbeed9;
  --color-error:          #b00020;
  --color-error-text:     #b00020;
  --color-error-soft:     #fbe4e7;
  --color-info:           #1f5fa8;
  --color-info-text:      #1f5fa8;
  --color-info-soft:      #e4eefb;
  --color-voided-text:    #6b6b85;
  --color-voided-soft:    #eef0f4;

  /* ---------- Color: functional + aliases ---------- */
  --color-focus:    var(--color-primary);
  --color-link:     var(--color-primary);
  --color-overlay:  rgb(18 19 26 / 0.45);
  --color-image-mat:#ffffff;
  --color-fg:          var(--color-text);
  --color-muted:       var(--color-text-muted);
  --color-primary-fg:  var(--color-on-primary);
  --color-ok:          var(--color-success);
  --color-warn:        var(--color-warning);

  /* ---------- Typography ---------- */
  --font-sans: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue',
               Arial, 'Noto Sans', sans-serif;
  --font-mono: ui-monospace, 'SF Mono', 'Source Code Pro', Menlo, Monaco,
               Consolas, 'Courier New', monospace;
  --font: var(--font-sans);
  --font-size-xs: .75rem;  --font-size-sm: .875rem; --font-size-base: 1rem;
  --font-size-md: 1.125rem;--font-size-lg: 1.25rem; --font-size-xl: 1.5rem;
  --font-size-2xl: 1.875rem; --font-size-3xl: 2.25rem;
  --line-height-tight: 1.2; --line-height-snug: 1.35;
  --line-height-normal: 1.6; --line-height-relaxed: 1.75;
  --font-weight-regular: 400; --font-weight-medium: 600; --font-weight-bold: 700;
  --letter-spacing-tight: -.01em; --letter-spacing-caps: .04em;
  --font-numeric-tabular: tabular-nums;
  --math-scale: 1.05;

  /* ---------- Spacing ---------- */
  --space-0: 0; --space-1: .25rem; --space-2: .5rem; --space-3: 1rem;
  --space-4: 1.5rem; --space-5: 2rem; --space-6: 3rem; --space-7: 4rem;

  /* ---------- Radius ---------- */
  --radius-none: 0; --radius-sm: 4px; --radius-md: 6px; --radius-lg: 10px;
  --radius-pill: 999px; --radius: var(--radius-md);

  /* ---------- Shadow ---------- */
  --shadow-none: none;
  --shadow-sm: 0 1px 2px rgb(18 19 26 / .06);
  --shadow-md: 0 2px 8px rgb(18 19 26 / .10);
  --shadow-lg: 0 8px 28px rgb(18 19 26 / .16);
  --shadow-focus: 0 0 0 3px var(--color-primary-soft);

  /* ---------- Z-index ---------- */
  --z-base: 0; --z-sticky: 100; --z-dropdown: 200;
  --z-overlay: 300; --z-modal: 310; --z-toast: 400;

  /* ---------- Breakpoints (documentary; see §4.5) ---------- */
  --bp-sm: 480px; --bp-md: 720px; --bp-lg: 960px; --bp-xl: 1280px;
  --maxw: 960px;

  /* ---------- Motion (see §7) ---------- */
  --duration-fast: 120ms; --duration-base: 200ms;
  --ease-standard: cubic-bezier(.2, 0, 0, 1);
}

/* Dark theme contract (ships later) — see §2.4 for full block */
[data-theme="dark"] {
  --color-bg: #12131a; --color-surface: #1a1c26; --color-surface-raised: #232634;
  --color-surface-sunken: #0e0f16; --color-border: #3a3d4d; --color-border-strong: #4c4f63;
  --color-text: #e6e8f0; --color-text-muted: #a6a9bd; --color-text-subtle: #8d90a6;
  --color-text-inverse: #12131a;
  --color-primary: #8fb0ff; --color-primary-strong: #aec4ff; --color-primary-soft: #17223d;
  --color-on-primary: #0e0f16;
  --color-success: #5cc98c; --color-success-text: #9fe0bb; --color-success-soft: #15301d;
  --color-warning: #e0a44d; --color-warning-text: #f0c98a; --color-warning-soft: #2e2410;
  --color-error: #f2899a; --color-error-text: #f6b3bf; --color-error-soft: #2e1419;
  --color-info: #7db0ec; --color-info-text: #aaccf5; --color-info-soft: #13243a;
  --color-voided-text: #8d90a6; --color-voided-soft: #1f2230;
  --color-overlay: rgb(0 0 0 / .6);
  --shadow-sm: 0 1px 2px rgb(0 0 0 / .5);
  --shadow-md: 0 2px 8px rgb(0 0 0 / .55);
  --shadow-lg: 0 8px 28px rgb(0 0 0 / .65);
}
```

### 5.4 How CSS Modules consume tokens

CSS Modules scope **class names**; they do **not** scope or isolate custom properties — `var(--*)`
resolves against the cascade exactly as in plain CSS, so a `.module.css` references tokens directly.
Example: the exam-runner choice cell, migrated from the global `.choice` rules.

```css
/* frontend/src/features/runner/Choice.module.css */
.choice {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 44px;                 /* touch target (Principle 4) */
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-base); /* 16px floor → inline KaTeX stays legible */
  line-height: var(--line-height-snug);
  color: var(--color-text);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.letter { font-weight: var(--font-weight-medium); }

/* Selected: NOT colour-alone — tinted fill + accent border + the radio's own checked state */
.choice[aria-checked='true'] {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
}

/* Review states pair colour with an icon/label rendered in the markup */
.choice[data-result='correct']   { background: var(--color-success-soft); border-color: var(--color-success); }
.choice[data-result='incorrect'] { background: var(--color-error-soft);   border-color: var(--color-error); }

.choice:focus-visible { outline: 3px solid var(--color-focus); outline-offset: 2px; }
```

```tsx
// Usage
import styles from './Choice.module.css'
<label className={styles.choice} data-result={result}>
  <span className={styles.letter}>{letter}</span>
  <Tex tex={choiceLatex} />
</label>
```

> **Theming a token *for one component*** (rare): set the custom property on the component root and
> children inherit it — e.g. `.voidedRow { --color-text: var(--color-voided-text); }` recolors its
> prose *and its KaTeX math* in one line, because both read `--color-text`. Prefer the standard
> tokens; reach for local overrides only for genuinely local semantics like this.

---

## 6. Theming (light/dark contract)

- **Mechanism.** Light is the default `:root`. Dark is the `[data-theme="dark"]` override block in
  `tokens.css` (§2.4 / §5.3). Set the attribute on `<html>`:
  `document.documentElement.setAttribute('data-theme', 'dark')`. Because every component reads
  tokens (Principle 5), nothing else changes — the whole app, **including KaTeX math** (glyphs
  inherit `--color-text`), re-themes from this one attribute.

- **Why an explicit attribute, not just media query.** An attribute lets a future settings toggle
  pin a theme regardless of OS, and lets us QA dark before shipping it to users. The contract exists
  now; the *toggle UI* and *persistence* are a later phase.

- **`prefers-color-scheme` default.** When/if dark ships, honor the OS preference as the initial
  value *without* forcing it, so an explicit user choice still wins:

  ```css
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme]) {
      /* same overrides as [data-theme="dark"] — keep the two blocks in sync,
         or apply data-theme via a tiny inline <head> script to avoid duplication
         and a flash of the wrong theme (FOUC). */
    }
  }
  ```

  Recommended implementation: a 3-line blocking script in `index.html` `<head>` that reads
  `localStorage.theme ?? matchMedia('(prefers-color-scheme: dark)')` and sets `data-theme` before
  first paint. This avoids both FOUC and duplicating the override block.

- **`color-scheme` property.** Set `:root { color-scheme: light; }` and
  `[data-theme="dark"] { color-scheme: dark; }` so native form controls, scrollbars, and the
  `<input>` UA styling match the theme.

- **Invariant tokens.** Spacing, radius, type, z-index, breakpoints, and `--math-scale` are
  theme-independent and live only in `:root`. Only color and shadow tokens appear in the dark block.

---

## 7. Motion

Motion is **minimal and purposeful** (Principles 2 & 3) — it confirms an action or eases a state
change, and it is *never* decorative or attention-grabbing during a timed test. Specifically: **the
timer never animates**, and nothing loops or pulses in the runner.

### 7.1 Tokens (standardize on one duration pair + one easing)

```css
--duration-fast: 120ms; /* hovers, focus, button/active feedback, checkbox toggles */
--duration-base: 200ms; /* entrances: dropdowns, modal/scrim, toast in/out */
--ease-standard: cubic-bezier(.2, 0, 0, 1); /* calm decelerate; the one curve we use */
```

Use `--duration-fast` for state on existing elements, `--duration-base` for things appearing or
leaving. Animate only cheap, non-layout properties — `opacity` and `transform` — to protect the
< 2 s interactive budget and avoid jank on tablets. Don't animate `width`/`height`/`top`/`left`.

```css
.button { transition: background-color var(--duration-fast) var(--ease-standard),
                      border-color var(--duration-fast) var(--ease-standard); }
.dialog { animation: fade-scale var(--duration-base) var(--ease-standard); }
@keyframes fade-scale { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: none; } }
```

### 7.2 `prefers-reduced-motion` (required)

Honor the OS reduced-motion setting globally. Transitions of *color/opacity* for feedback may remain
near-instant; **movement** is removed.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: .01ms !important;
    scroll-behavior: auto !important;
  }
}
```

> Loading states use a static "Loading…" label or a non-spinning indicator under reduced motion;
> the existing `.spinner` element should degrade to text rather than rotate. No spinner is acceptable
> on the exam runner regardless — a detached timer must never be obscured by a spinner overlay.

---

## 8. Implementation checklist

- [ ] Create `frontend/src/styles/tokens.css` from §5.3 verbatim.
- [ ] Import it in `main.tsx` **before** `index.css` (after the KaTeX CSS).
- [ ] Add the global `.katex` / `.katex-display` / `.katex-error` rules (§3.5) to `index.css`.
- [ ] Add the `prefers-reduced-motion` block (§7.2) and `color-scheme` declarations (§6) to `index.css`.
- [ ] Leave existing `--color-*`/`--space-*`/`--radius`/`--maxw`/`--font` consumers working via the
      back-compat aliases; migrate component blocks out of `index.css` into `*.module.css`
      incrementally, replacing raw values with tokens as you go.
- [ ] Defer the dark **toggle UI + persistence**; the dark **token contract** is already defined and
      QA-able via `data-theme="dark"`.

## 9. Open items / future

- Dark-mode rollout: ship the toggle + `localStorage` persistence + the FOUC-avoidance head script
  (§6); QA raster problem-image mats (`--color-image-mat`, §2.4) before enabling.
- A high-contrast / forced-colors (`@media (forced-colors: active)`) pass for the runner is a good
  follow-up given the exam context, but is out of scope for v1.
- If a brand/marketing surface ever needs a display typeface, that is the only justification to add a
  web font — and it must be `font-display: swap`, subset, and kept off the exam runner path.
