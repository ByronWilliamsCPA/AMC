/**
 * Render a LaTeX string with KaTeX, safely and React-friendly.
 *
 * Uses `katex.renderToString` inside a `useMemo` (one render per input) and
 * injects the result once, rather than the global `renderMathInElement` scanner
 * that fights React's reconciliation. `throwOnError: false` means malformed TeX
 * renders as a visible error string instead of crashing the runner mid-exam.
 *
 * KaTeX output is produced from the LaTeX source by KaTeX itself (not arbitrary
 * user HTML), so injecting it is safe. KaTeX's CSS is imported once at the app
 * root (see `main.tsx`).
 */
import katex from 'katex'
import { useMemo } from 'react'

export interface TexProps {
  /** The LaTeX source to render. */
  tex: string
  /** Render as a display (block) equation rather than inline. */
  display?: boolean
}

export function Tex({ tex, display = false }: TexProps) {
  const html = useMemo(
    () =>
      katex.renderToString(tex, {
        displayMode: display,
        throwOnError: false,
        output: 'htmlAndMathml',
      }),
    [tex, display]
  )

  return (
    <span
      // Safe: `html` is KaTeX's own output for `tex`, not arbitrary user HTML.
      dangerouslySetInnerHTML={{ __html: html }}
      data-testid="math"
    />
  )
}
