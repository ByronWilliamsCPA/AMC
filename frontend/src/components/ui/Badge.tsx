/**
 * Badge / Tag: a compact status pill (verdict, voided, role). The child text
 * carries the meaning; the tone colour is purely decorative, so it stays
 * accessible without colour (WCAG 1.4.1).
 */
import type { ReactNode } from 'react'
import { cx } from '@/lib/cx'
import styles from './Badge.module.css'

export type BadgeTone = 'neutral' | 'success' | 'warning' | 'danger' | 'info'

export interface BadgeProps {
  tone?: BadgeTone
  children: ReactNode
}

export function Badge({ tone = 'neutral', children }: BadgeProps) {
  return <span className={cx(styles.badge, styles[tone])}>{children}</span>
}
