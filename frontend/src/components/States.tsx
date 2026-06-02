/**
 * Shared loading and error presentational components.
 *
 * Status is conveyed by text (and ARIA), never by colour alone, so it remains
 * accessible - the convention this app follows everywhere.
 */
import type { ReactNode } from 'react'

export function Spinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <output className="spinner" aria-live="polite">
      {label}
    </output>
  )
}

export function ErrorState({
  title = 'Something went wrong',
  children,
}: {
  title?: string
  children?: ReactNode
}) {
  return (
    <div className="error-state" role="alert">
      <strong>{title}</strong>
      {children}
    </div>
  )
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="empty-state">{children}</p>
}
