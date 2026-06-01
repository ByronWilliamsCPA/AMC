/**
 * Question palette: a grid of problem numbers showing answered / flagged /
 * current / voided state. Status is conveyed by text (aria-label) and shape,
 * not colour alone.
 *
 * Keyboard model (roving tabindex): the palette is a single Tab stop - exactly
 * one cell is tabbable (the current question). Arrow keys move focus between
 * cells (Left/Right by one, Up/Down by a row of five), Home/End jump to the
 * first/last, and Enter/Space (native button activation) selects.
 */
import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { cx } from '@/lib/cx'
import type { RunnerState } from '@/features/exam/runnerState'
import styles from './Palette.module.css'

/** Columns in the palette grid (mirrors the CSS `repeat(5, 1fr)`). */
const COLUMNS = 5

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
  const count = state.answers.length
  const currentIndex = state.current
  const cellRefs = useRef<(HTMLButtonElement | null)[]>([])
  // Which cell is the single tab stop. Follows the current question so tabbing
  // into the palette lands on it.
  const [focusIndex, setFocusIndex] = useState(currentIndex)

  useEffect(() => {
    setFocusIndex(currentIndex)
  }, [currentIndex])

  const moveFocus = (target: number) => {
    const clamped = Math.max(0, Math.min(count - 1, target))
    setFocusIndex(clamped)
    cellRefs.current[clamped]?.focus()
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    switch (event.key) {
      case 'ArrowRight':
        event.preventDefault()
        moveFocus(index + 1)
        break
      case 'ArrowLeft':
        event.preventDefault()
        moveFocus(index - 1)
        break
      case 'ArrowDown':
        event.preventDefault()
        moveFocus(index + COLUMNS)
        break
      case 'ArrowUp':
        event.preventDefault()
        moveFocus(index - COLUMNS)
        break
      case 'Home':
        event.preventDefault()
        moveFocus(0)
        break
      case 'End':
        event.preventDefault()
        moveFocus(count - 1)
        break
      default:
        break
    }
  }

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
                ref={(el) => {
                  cellRefs.current[index] = el
                }}
                className={cx(
                  styles.cell,
                  answered && styles.answered,
                  flagged && styles.flagged,
                  isCurrent && styles.current,
                  isVoided && styles.voided
                )}
                tabIndex={index === focusIndex ? 0 : -1}
                aria-current={isCurrent ? 'true' : undefined}
                aria-label={`Question ${number}: ${statusLabel(answered, flagged, isVoided)}`}
                onClick={() => onSelect(index)}
                onKeyDown={(event) => handleKeyDown(event, index)}
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
