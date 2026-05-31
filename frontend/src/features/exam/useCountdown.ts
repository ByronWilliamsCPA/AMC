/**
 * Countdown timer driven by an absolute deadline.
 *
 * #CRITICAL: timing: the timer is computed from an absolute deadline
 * (`startedAt + durationSec`), not by decrementing a counter, so it does not
 * drift and does not pause when the tab is backgrounded — a backgrounded
 * `setInterval` is throttled, and a decrement-based timer would under-count.
 * #VERIFY: on reaching zero, `onExpire` is fired exactly once (guarded), so the
 * runner auto-submits a single time.
 */
import { useEffect, useRef, useState } from 'react'

export interface Countdown {
  /** Whole seconds remaining (never negative). */
  remaining: number
  /** Whether the deadline has passed. */
  expired: boolean
}

export function useCountdown(
  startedAtMs: number,
  durationSec: number,
  onExpire: () => void
): Countdown {
  const deadline = startedAtMs + durationSec * 1000
  const [remaining, setRemaining] = useState(() =>
    Math.max(0, Math.ceil((deadline - Date.now()) / 1000))
  )
  const firedRef = useRef(false)
  const onExpireRef = useRef(onExpire)
  onExpireRef.current = onExpire

  useEffect(() => {
    const tick = () => {
      const secs = Math.max(0, Math.ceil((deadline - Date.now()) / 1000))
      setRemaining(secs)
      if (secs <= 0 && !firedRef.current) {
        firedRef.current = true
        onExpireRef.current()
      }
    }
    tick()
    const id = window.setInterval(tick, 1000)
    return () => window.clearInterval(id)
  }, [deadline])

  return { remaining, expired: remaining <= 0 }
}

/** Format whole seconds as `M:SS` (or `H:MM:SS` past an hour). */
export function formatDuration(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(s / 3600)
  const minutes = Math.floor((s % 3600) / 60)
  const seconds = s % 60
  const mm = minutes.toString().padStart(hours > 0 ? 2 : 1, '0')
  const ss = seconds.toString().padStart(2, '0')
  return hours > 0 ? `${hours}:${mm}:${ss}` : `${mm}:${ss}`
}
