/**
 * Exam countdown chip.
 *
 * The visible time is a silent `role="timer"` (`aria-live="off"`) — announcing
 * every second would flood a screen reader. Instead a separate polite region
 * announces milestones as they're crossed (10/5/1 min, 30 s, time's up). The
 * urgency tier is shown by colour AND a text caption so it never rests on
 * colour alone.
 */
import { useEffect, useRef, useState } from 'react'
import { cx } from '@/lib/cx'
import { formatDuration } from '@/features/exam/useCountdown'
import styles from './Timer.module.css'

interface Milestone {
  at: number
  message: string
}

/** Announced once as the countdown crosses each threshold (descending). */
const MILESTONES: Milestone[] = [
  { at: 600, message: '10 minutes remaining' },
  { at: 300, message: '5 minutes remaining' },
  { at: 60, message: '1 minute remaining' },
  { at: 30, message: '30 seconds remaining' },
  { at: 0, message: "Time's up — submitting your test." },
]

function tier(remaining: number): 'normal' | 'caution' | 'warning' {
  if (remaining <= 60) return 'warning'
  if (remaining <= 300) return 'caution'
  return 'normal'
}

const CAPTION: Record<'normal' | 'caution' | 'warning', string | null> = {
  normal: null,
  caution: 'Time running low',
  warning: 'Almost out of time',
}

export interface TimerProps {
  /** Whole seconds remaining. */
  remaining: number
}

export function Timer({ remaining }: TimerProps) {
  const announcedRef = useRef<Set<number>>(new Set())
  const [announcement, setAnnouncement] = useState('')

  useEffect(() => {
    for (const milestone of MILESTONES) {
      if (remaining <= milestone.at && !announcedRef.current.has(milestone.at)) {
        announcedRef.current.add(milestone.at)
        setAnnouncement(milestone.message)
      }
    }
  }, [remaining])

  const level = tier(remaining)
  const caption = CAPTION[level]
  const formatted = formatDuration(remaining)

  return (
    <div className={cx(styles.timer, level !== 'normal' && styles[level])}>
      <span
        className={styles.time}
        role="timer"
        aria-live="off"
        aria-label={`Time remaining: ${formatted}`}
      >
        {formatted}
      </span>
      {caption !== null && <span className={styles.caption}>{caption}</span>}
      <span className="visually-hidden" role="status" aria-live="polite">
        {announcement}
      </span>
    </div>
  )
}
