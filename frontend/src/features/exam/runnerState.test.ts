import { describe, expect, it } from 'vitest'
import {
  answeredCount,
  initRunner,
  runnerReducer,
  type RunnerState,
} from '@/features/exam/runnerState'

function freshState(): RunnerState {
  return initRunner(3)
}

describe('runnerReducer', () => {
  it('initialises blank answers and flags', () => {
    const state = initRunner(5)
    expect(state.answers).toEqual([null, null, null, null, null])
    expect(state.flags).toEqual([false, false, false, false, false])
    expect(state.current).toBe(0)
    expect(state.phase).toBe('active')
  })

  it('records and clears an answer', () => {
    let state = freshState()
    state = runnerReducer(state, { type: 'answer', index: 1, choice: 'C' })
    expect(state.answers[1]).toBe('C')
    expect(answeredCount(state)).toBe(1)
    state = runnerReducer(state, { type: 'clearAnswer', index: 1 })
    expect(state.answers[1]).toBeNull()
    expect(answeredCount(state)).toBe(0)
  })

  it('toggles a flag', () => {
    let state = freshState()
    state = runnerReducer(state, { type: 'toggleFlag', index: 2 })
    expect(state.flags[2]).toBe(true)
    state = runnerReducer(state, { type: 'toggleFlag', index: 2 })
    expect(state.flags[2]).toBe(false)
  })

  it('navigates with goto/next/prev and clamps bounds', () => {
    let state = freshState()
    state = runnerReducer(state, { type: 'next' })
    expect(state.current).toBe(1)
    state = runnerReducer(state, { type: 'goto', index: 99 })
    expect(state.current).toBe(2) // clamped to last
    state = runnerReducer(state, { type: 'next' })
    expect(state.current).toBe(2) // can't go past last
    state = runnerReducer(state, { type: 'goto', index: -5 })
    expect(state.current).toBe(0) // clamped to first
    state = runnerReducer(state, { type: 'prev' })
    expect(state.current).toBe(0)
  })

  it('freezes edits once submitting', () => {
    let state = freshState()
    state = runnerReducer(state, { type: 'startSubmit' })
    expect(state.phase).toBe('submitting')
    state = runnerReducer(state, { type: 'answer', index: 0, choice: 'A' })
    expect(state.answers[0]).toBeNull() // edit ignored after submit
  })

  it('startSubmit is idempotent (only the first transition counts)', () => {
    let state = freshState()
    state = runnerReducer(state, { type: 'startSubmit' })
    state = runnerReducer(state, { type: 'submitted' })
    expect(state.phase).toBe('review')
    // A second startSubmit from review does not revert to submitting.
    state = runnerReducer(state, { type: 'startSubmit' })
    expect(state.phase).toBe('review')
  })
})
