/**
 * Pure state machine for the timed exam runner.
 *
 * Kept free of React and the network so it can be unit-tested directly (the
 * ADR-002 testability rationale): answers, flags, navigation, and phase
 * transitions are all reducer actions. The submit *payload* is modelled in the
 * exact `ExamSubmission` shape (`answers`, `flags`, `time_used_sec`) so the hook
 * can post it without translation.
 */

export type RunnerPhase = 'active' | 'submitting' | 'review'

export interface RunnerState {
  /** Per-problem answers (null = blank), length == numProblems. */
  answers: (string | null)[]
  /** Per-problem flag state, length == numProblems. */
  flags: boolean[]
  /** 0-based index of the current problem. */
  current: number
  /** Number of problems. */
  numProblems: number
  phase: RunnerPhase
}

export type RunnerAction =
  | { type: 'answer'; index: number; choice: string }
  | { type: 'clearAnswer'; index: number }
  | { type: 'toggleFlag'; index: number }
  | { type: 'goto'; index: number }
  | { type: 'next' }
  | { type: 'prev' }
  | { type: 'startSubmit' }
  | { type: 'submitted' }

/** Build the initial runner state for an exam with `numProblems` problems. */
export function initRunner(numProblems: number): RunnerState {
  return {
    answers: Array<string | null>(numProblems).fill(null),
    flags: Array<boolean>(numProblems).fill(false),
    current: 0,
    numProblems,
    phase: 'active',
  }
}

function clampIndex(index: number, numProblems: number): number {
  if (index < 0) return 0
  if (index >= numProblems) return numProblems - 1
  return index
}

export function runnerReducer(state: RunnerState, action: RunnerAction): RunnerState {
  // Once submitting/reviewing, answer/flag edits are frozen.
  const editable = state.phase === 'active'

  switch (action.type) {
    case 'answer': {
      if (!editable) return state
      const answers = state.answers.slice()
      answers[action.index] = action.choice
      return { ...state, answers }
    }
    case 'clearAnswer': {
      if (!editable) return state
      const answers = state.answers.slice()
      answers[action.index] = null
      return { ...state, answers }
    }
    case 'toggleFlag': {
      if (!editable) return state
      const flags = state.flags.slice()
      flags[action.index] = !flags[action.index]
      return { ...state, flags }
    }
    case 'goto':
      return { ...state, current: clampIndex(action.index, state.numProblems) }
    case 'next':
      return { ...state, current: clampIndex(state.current + 1, state.numProblems) }
    case 'prev':
      return { ...state, current: clampIndex(state.current - 1, state.numProblems) }
    case 'startSubmit':
      // Idempotent: only the first transition out of 'active' takes effect.
      return state.phase === 'active' ? { ...state, phase: 'submitting' } : state
    case 'submitted':
      return { ...state, phase: 'review' }
    default:
      return state
  }
}

/** Count answered (non-null) problems. */
export function answeredCount(state: RunnerState): number {
  return state.answers.filter((a) => a !== null).length
}
