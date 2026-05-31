/**
 * Question palette: a grid of problem numbers showing answered / flagged /
 * current / voided state. Status is conveyed by text (aria-label) and shape, not
 * colour alone, and the grid is keyboard-navigable.
 */
import { cx } from '@/lib/cx'
import type { RunnerState } from '@/features/exam/runnerState'
import styles from './Palette.module.css'

export interface PaletteProps {
  state: RunnerState
  voided: number[]
  onSelect: (index: number) => void
}

function statusLabel(answered: boolean, flagged: boolean, voided: boolean): string {
  if (voided) return 'voided'
  const parts: string[] = [answered ? 'answered' : 'unanswered']
  if (flagged) parts.push('flagged')
  return parts.join(', ')
}

export function Palette({ state, voided, onSelect }: PaletteProps) {
  const voidedSet = new Set(voided)
  return (
    <nav className={styles.palette} aria-label="Question navigator">
      <ul className={styles.list}>
        {state.answers.map((answer, index) => {
          const number = index + 1
          const isVoided = voidedSet.has(number)
          const flagged = state.flags[index]
          const answered = answer !== null
          const isCurrent = state.current === index
          return (
            <li key={number}>
              <button
                type="button"
                className={cx(
                  styles.cell,
                  answered && styles.answered,
                  flagged && styles.flagged,
                  isCurrent && styles.current,
                  isVoided && styles.voided
                )}
                aria-current={isCurrent ? 'true' : undefined}
                aria-label={`Question ${number}: ${statusLabel(answered, flagged, isVoided)}`}
                onClick={() => onSelect(index)}
              >
                {number}
                {flagged && <span aria-hidden="true"> ⚑</span>}
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
