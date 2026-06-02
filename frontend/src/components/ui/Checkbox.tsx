/**
 * Checkbox: a labelled boolean. The native input sits inside the `<label>`, so
 * the whole row is a click target and the checked state is conveyed by the
 * native glyph (not colour alone).
 */
import type { InputHTMLAttributes, ReactNode } from 'react'
import { cx } from '@/lib/cx'
import styles from './Checkbox.module.css'

export interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: ReactNode
}

export function Checkbox({ label, className, ...rest }: CheckboxProps) {
  return (
    <label className={styles.checkbox}>
      <input type="checkbox" className={cx(styles.input, className)} {...rest} />
      <span>{label}</span>
    </label>
  )
}
