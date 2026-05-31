/**
 * RadioGroup: a labelled set of native radios. Used for the exam's A–E answer
 * choices. Native radios give roving focus and arrow-key selection for free
 * (WCAG 2.1.1); a disabled `<fieldset>` freezes the whole group (e.g. after an
 * exam is submitted). Option labels are arbitrary nodes so callers can render
 * KaTeX-typeset choices.
 */
import type { ReactNode } from 'react'
import { cx } from '@/lib/cx'
import styles from './RadioGroup.module.css'

export interface RadioOption {
  value: string
  label: ReactNode
}

export interface RadioGroupProps {
  /** Accessible group name, e.g. "Answer choices for problem 7". */
  legend: string
  /** Native grouping name; only one radio per name can be checked. */
  name: string
  /** The selected value, or null when nothing is chosen. */
  value: string | null
  options: RadioOption[]
  disabled?: boolean
  onChange: (value: string) => void
}

export function RadioGroup({
  legend,
  name,
  value,
  options,
  disabled = false,
  onChange,
}: RadioGroupProps) {
  return (
    <fieldset className={styles.group} role="radiogroup" aria-label={legend} disabled={disabled}>
      {options.map((option) => {
        const checked = value === option.value
        return (
          <label key={option.value} className={cx(styles.option, checked && styles.selected)}>
            <input
              type="radio"
              className={styles.input}
              name={name}
              value={option.value}
              checked={checked}
              onChange={() => onChange(option.value)}
              disabled={disabled}
            />
            {option.label}
          </label>
        )
      })}
    </fieldset>
  )
}
