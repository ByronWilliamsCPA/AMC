/**
 * Card: a bordered content container. Presentational only - it is never itself
 * the click target; an interactive card holds one real link/button inside and
 * lifts that control's focus ring via `:focus-within`.
 */
import type { ElementType, HTMLAttributes, ReactNode } from 'react'
import { cx } from '@/lib/cx'
import styles from './Card.module.css'

export interface CardProps extends HTMLAttributes<HTMLElement> {
  /** The element to render as (e.g. 'article', 'li', 'section'). */
  as?: ElementType
  interactive?: boolean
  children: ReactNode
}

export function Card({
  as: Tag = 'div',
  interactive = false,
  className,
  children,
  ...rest
}: CardProps) {
  return (
    <Tag className={cx(styles.card, interactive && styles.interactive, className)} {...rest}>
      {children}
    </Tag>
  )
}
