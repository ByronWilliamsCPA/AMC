/**
 * Alert / Callout: a standing message box with severities. The severity word
 * ("Warning:", "Error:", …) is rendered as visible text so meaning never rests
 * on colour alone. `role` defaults to "alert" for warning/error (announced when
 * they appear in response to an action) and "status" otherwise.
 */
import type { ReactNode } from 'react'
import { cx } from '@/lib/cx'
import styles from './Alert.module.css'

export type AlertSeverity = 'info' | 'success' | 'warning' | 'error'

export interface AlertProps {
  severity: AlertSeverity
  /** Override the default prefix word. */
  prefix?: string
  /** Override the implicit live-region role. */
  role?: 'status' | 'alert'
  children: ReactNode
}

const DEFAULT_PREFIX: Record<AlertSeverity, string> = {
  info: 'Note',
  success: 'Success',
  warning: 'Warning',
  error: 'Error',
}

export function Alert({ severity, prefix, role, children }: AlertProps) {
  const resolvedRole = role ?? (severity === 'warning' || severity === 'error' ? 'alert' : 'status')
  return (
    <div className={cx(styles.alert, styles[severity])} role={resolvedRole}>
      <span className={styles.prefix}>{prefix ?? DEFAULT_PREFIX[severity]}:</span>
      <span>{children}</span>
    </div>
  )
}
