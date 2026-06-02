/**
 * Select: a labelled native `<select>`. Native gives keyboard and
 * screen-reader support for free; we only add the label association and
 * token-driven styling.
 */
import { useId, type SelectHTMLAttributes } from 'react'
import { cx } from '@/lib/cx'
import styles from './Select.module.css'

export interface SelectOption {
  value: string
  label: string
}

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'id'> {
  label: string
  options: SelectOption[]
}

export function Select({ label, options, className, ...rest }: SelectProps) {
  const id = useId()
  return (
    <div className={styles.field}>
      <label htmlFor={id} className={styles.label}>
        {label}
      </label>
      <select id={id} className={cx(styles.select, className)} {...rest}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  )
}
