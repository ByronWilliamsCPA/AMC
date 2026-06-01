import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Tex } from './Tex'

describe('Tex', () => {
  it('emits a MathML tree for screen readers (output: htmlAndMathml)', () => {
    const { container } = render(<Tex tex="x^2 + 1" />)
    // KaTeX renders the visual HTML plus a parallel <math> (MathML) tree that
    // assistive tech reads; guard against an output-mode regression.
    expect(container.querySelector('math')).not.toBeNull()
  })

  it('renders display math in a scrollable .katex-display block', () => {
    const { container } = render(<Tex tex="\frac{1}{2}" display />)
    expect(container.querySelector('.katex-display')).not.toBeNull()
    expect(container.querySelector('math')).not.toBeNull()
  })

  it('does not throw on malformed LaTeX (renders a visible error instead)', () => {
    // throwOnError: false - a bad problem must not crash the runner mid-exam.
    expect(() => render(<Tex tex="\frac{1}{" />)).not.toThrow()
    expect(screen.getByTestId('math')).toBeInTheDocument()
  })
})
