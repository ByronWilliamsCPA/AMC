/**
 * TextField: a labelled text input with optional hint and error, wired for
 * accessibility by construction (label association, `aria-invalid`, and
 * `aria-describedby` joining the hint + error). Native constraints
 * (`type`, `required`, `minLength`, `autoComplete`) pass straight through.
 */
import { useId, type InputHTMLAttributes } from 'react'
import { cx } from '@/lib/cx'
import styles from './TextField.module.css'

export interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> {
  label: string
  /** Optional helper text shown under the field. */
  hint?: string
  /** When set, marks the field invalid and shows the message. */
  error?: string
  /** Hide the visible label (still read by screen readers). */
  hiddenLabel?: boolean
}

export function TextField({
  label,
  hint,
  error,
  hiddenLabel = false,
  className,
  ...rest
}: TextFieldProps) {
  const id = useId()
  const hintId = `${id}-hint`
  const errorId = `${id}-error`
  const describedBy = cx(hint ? hintId : undefined, error ? errorId : undefined) || undefined

  return (
    <div className={styles.field}>
      <label htmlFor={id} className={hiddenLabel ? 'visually-hidden' : styles.label}>
        {label}
      </label>
      <input
        id={id}
        className={cx(styles.input, className)}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        {...rest}
      />
      {hint !== undefined && (
        <span id={hintId} className={styles.hint}>
          {hint}
        </span>
      )}
      {error !== undefined && (
        <span id={errorId} className={styles.error} role="alert">
          {error}
        </span>
      )}
    </div>
  )
}
