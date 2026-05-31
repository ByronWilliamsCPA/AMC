import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Palette } from '@/features/exam/Palette'
import { initRunner, runnerReducer } from '@/features/exam/runnerState'

describe('Palette', () => {
  it('labels each cell with its answered/flagged/voided status', () => {
    let state = initRunner(3)
    state = runnerReducer(state, { type: 'answer', index: 0, choice: 'A' })
    state = runnerReducer(state, { type: 'toggleFlag', index: 1 })

    render(<Palette state={state} voided={[3]} onSelect={() => {}} />)

    expect(screen.getByRole('button', { name: /Question 1: answered/ })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /Question 2: unanswered, flagged/ })
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Question 3: voided/ })).toBeInTheDocument()
  })

  it('calls onSelect with the chosen index', async () => {
    const onSelect = vi.fn()
    render(<Palette state={initRunner(3)} voided={[]} onSelect={onSelect} />)
    await userEvent.click(screen.getByRole('button', { name: /Question 2/ }))
    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('marks the current question with aria-current', () => {
    const state = { ...initRunner(3), current: 2 }
    render(<Palette state={state} voided={[]} onSelect={() => {}} />)
    const current = screen.getByRole('button', { name: /Question 3/ })
    expect(current).toHaveAttribute('aria-current', 'true')
  })

  it('is a single tab stop: only the current question is tabbable', () => {
    const state = { ...initRunner(6), current: 2 }
    render(<Palette state={state} voided={[]} onSelect={() => {}} />)
    expect(screen.getByRole('button', { name: /Question 3/ })).toHaveAttribute('tabindex', '0')
    expect(screen.getByRole('button', { name: /Question 1/ })).toHaveAttribute('tabindex', '-1')
    expect(screen.getByRole('button', { name: /Question 6/ })).toHaveAttribute('tabindex', '-1')
  })

  it('moves focus with arrow and Home/End keys (roving tabindex)', async () => {
    const user = userEvent.setup()
    render(<Palette state={initRunner(6)} voided={[]} onSelect={() => {}} />)

    const q1 = screen.getByRole('button', { name: /Question 1/ })
    q1.focus()
    expect(q1).toHaveFocus()

    // Right moves by one.
    await user.keyboard('{ArrowRight}')
    expect(screen.getByRole('button', { name: /Question 2/ })).toHaveFocus()

    // Down moves by a row of five: from Question 2 (index 1) to index 6, which
    // is out of range for 6 items, so it clamps to the last (Question 6).
    await user.keyboard('{ArrowDown}')
    expect(screen.getByRole('button', { name: /Question 6/ })).toHaveFocus()

    // End / Home jump to last / first.
    await user.keyboard('{Home}')
    expect(screen.getByRole('button', { name: /Question 1/ })).toHaveFocus()
    await user.keyboard('{End}')
    expect(screen.getByRole('button', { name: /Question 6/ })).toHaveFocus()
  })
})
