/**
 * Modal dialog (and bottom-sheet variant).
 *
 * Accessible modal: `role="dialog"` + `aria-modal`, labelled by its title.
 * While open it traps focus, closes on Esc and on backdrop click, locks body
 * scroll, and restores focus to the previously focused element on close.
 */
import { useEffect, useId, useRef, type KeyboardEvent, type ReactNode } from 'react'
import { cx } from '@/lib/cx'
import styles from './Dialog.module.css'

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  placement?: 'center' | 'bottom'
  children: ReactNode
}

export function Dialog({ open, onClose, title, placement = 'center', children }: DialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const previouslyFocused = useRef<HTMLElement | null>(null)
  const titleId = useId()

  useEffect(() => {
    if (!open) return
    previouslyFocused.current = document.activeElement as HTMLElement | null
    const node = dialogRef.current
    const focusables = node?.querySelectorAll<HTMLElement>(FOCUSABLE)
    if (focusables && focusables.length > 0) focusables[0].focus()
    else node?.focus()

    const { overflow } = document.body.style
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = overflow
      previouslyFocused.current?.focus()
    }
  }, [open])

  if (!open) return null

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Escape') {
      event.stopPropagation()
      onClose()
      return
    }
    if (event.key !== 'Tab') return
    const node = dialogRef.current
    if (node === null) return
    const focusables = Array.from(node.querySelectorAll<HTMLElement>(FOCUSABLE))
    if (focusables.length === 0) {
      event.preventDefault()
      return
    }
    const first = focusables[0]
    const last = focusables[focusables.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  return (
    // Backdrop click-to-dismiss is a mouse convenience; the keyboard equivalent
    // (Esc) is handled on the dialog, and focus is trapped inside it — so the
    // static-interaction lint warning is a false positive here.
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions
    <div
      className={styles.overlay}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <div
        ref={dialogRef}
        className={cx(styles.dialog, placement === 'bottom' && styles.sheet)}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
      >
        <h2 id={titleId} className={styles.title}>
          {title}
        </h2>
        {children}
      </div>
    </div>
  )
}
