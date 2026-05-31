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
})
