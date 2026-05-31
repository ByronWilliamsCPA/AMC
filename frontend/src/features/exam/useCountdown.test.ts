import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { formatDuration, useCountdown } from '@/features/exam/useCountdown'

describe('formatDuration', () => {
  it('formats minutes and seconds', () => {
    expect(formatDuration(0)).toBe('0:00')
    expect(formatDuration(9)).toBe('0:09')
    expect(formatDuration(75)).toBe('1:15')
    expect(formatDuration(3661)).toBe('1:01:01')
  })

  it('never goes negative', () => {
    expect(formatDuration(-5)).toBe('0:00')
  })
})

describe('useCountdown', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('counts down from the absolute deadline', () => {
    const start = Date.now()
    const onExpire = vi.fn()
    const { result } = renderHook(() => useCountdown(start, 10, onExpire))
    expect(result.current.remaining).toBe(10)

    act(() => {
      vi.advanceTimersByTime(3000)
    })
    expect(result.current.remaining).toBe(7)
    expect(onExpire).not.toHaveBeenCalled()
  })

  it('fires onExpire exactly once at zero', () => {
    const start = Date.now()
    const onExpire = vi.fn()
    renderHook(() => useCountdown(start, 2, onExpire))

    act(() => {
      vi.advanceTimersByTime(5000) // well past the deadline
    })
    expect(onExpire).toHaveBeenCalledTimes(1)

    act(() => {
      vi.advanceTimersByTime(5000) // keep ticking
    })
    // Still only fired once despite further ticks.
    expect(onExpire).toHaveBeenCalledTimes(1)
  })
})
