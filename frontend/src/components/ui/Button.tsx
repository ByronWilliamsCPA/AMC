/**
 * Button primitive (design prototype).
 *
 * The single styled action element — replaces raw `<button>` + the global
 * `button {}` rule. Always a real `<button>` (never a clickable div). Variants
 * map to local CSS-Module classes; ARIA state (`aria-busy`) drives the loading
 * presentation so visual and accessible state can't drift.
 */
import type { ButtonHTMLAttributes } from 'react'
import { cx } from '@/lib/cx'
import styles from './Button.module.css'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual emphasis. Default 'secondary'. */
  variant?: 'primary' | 'secondary' | 'subtle'
  /** Stretch to the container width. */
  block?: boolean
}

export function Button({
  variant = 'secondary',
  block = false,
  className,
  type = 'button',
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cx(
        styles.button,
        variant === 'primary' && styles.primary,
        variant === 'subtle' && styles.subtle,
        block && styles.block,
        className
      )}
      {...rest}
    />
  )
}
