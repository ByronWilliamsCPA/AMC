/**
 * The timed exam runner (US-001).
 *
 * Loads the key-free exam, drives the runner reducer, runs an absolute-deadline
 * countdown that auto-submits at zero, and on submit posts `{answers, flags,
 * time_used_sec}` and shows the graded review. The submit is guarded so the
 * timer and the manual button can never double-submit; a 409 from the server
 * (double submit) is treated as "already submitted".
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useReducer, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { ErrorState, Spinner } from '@/components/States'
import { Button, Dialog } from '@/components/ui'
import { ExamReview } from '@/features/exam/ExamReview'
import { Palette } from '@/features/exam/Palette'
import { Question } from '@/features/exam/Question'
import { answeredCount, initRunner, runnerReducer } from '@/features/exam/runnerState'
import { Timer } from '@/features/exam/Timer'
import { useCountdown } from '@/features/exam/useCountdown'
import type { ExamDetail, ExamResultResponse } from '@/client'
import { ApiError, getExam, submitExam } from '@/lib/endpoints'
import { queryKeys } from '@/lib/queryClient'
import styles from './ExamRunnerPage.module.css'

export function ExamRunnerPage() {
  const { examId = '' } = useParams()
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.exam(examId),
    queryFn: () => getExam(examId),
  })

  if (isLoading) return <Spinner label="Loading exam…" />
  if (isError || data === undefined) return <ErrorState title="Could not load this exam" />

  return <RunnerInner exam={data} />
}

function RunnerInner({ exam }: { exam: ExamDetail }) {
  const queryClient = useQueryClient()
  const [state, dispatch] = useReducer(runnerReducer, exam.num_problems, initRunner)
  const startedAtRef = useRef(Date.now())
  const [result, setResult] = useState<ExamResultResponse | null>(null)
  const [paletteOpen, setPaletteOpen] = useState(false)

  const submitMutation = useMutation({
    mutationFn: () => {
      const timeUsed = Math.round((Date.now() - startedAtRef.current) / 1000)
      return submitExam(exam.id, {
        answers: state.answers,
        flags: state.flags,
        time_used_sec: timeUsed,
      })
    },
    onSuccess: (graded) => {
      setResult(graded)
      dispatch({ type: 'submitted' })
      void queryClient.invalidateQueries({ queryKey: queryKeys.progress() })
    },
    onError: (error) => {
      // A 409 means the attempt was already submitted; treat as terminal.
      if (error instanceof ApiError && error.status === 409) {
        dispatch({ type: 'submitted' })
      }
    },
  })

  // Single submit entry point: flips phase to 'submitting' (idempotent in the
  // reducer) and fires the mutation once.
  const triggerSubmit = useCallback(() => {
    if (state.phase !== 'active') return
    dispatch({ type: 'startSubmit' })
    submitMutation.mutate()
  }, [state.phase, submitMutation])

  const { remaining } = useCountdown(startedAtRef.current, exam.duration_sec, triggerSubmit)

  if (state.phase === 'review' && result !== null) {
    return <ExamReview result={result} />
  }

  const problem = exam.problems[state.current]
  const frozen = state.phase !== 'active'

  return (
    <section className={styles.runner}>
      <header className={styles.header}>
        <h1>
          {exam.contest} {exam.year}
          {exam.variant}
        </h1>
        <Timer remaining={remaining} />
        <p className={styles.progress} aria-live="polite">
          {answeredCount(state)} of {state.numProblems} answered
        </p>
      </header>

      <div className={styles.paletteBar}>
        <Button type="button" aria-expanded={paletteOpen} onClick={() => setPaletteOpen(true)}>
          Questions ({answeredCount(state)}/{state.numProblems})
        </Button>
      </div>

      <Dialog
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        title="Question navigator"
        placement="bottom"
      >
        <Palette
          state={state}
          voided={exam.voided}
          onSelect={(index) => {
            dispatch({ type: 'goto', index })
            setPaletteOpen(false)
          }}
        />
      </Dialog>

      <div className={styles.body}>
        <div className={styles.sidebar}>
          <Palette
            state={state}
            voided={exam.voided}
            onSelect={(index) => dispatch({ type: 'goto', index })}
          />
        </div>

        <div>
          {problem !== undefined && (
            <Question
              problem={problem}
              selected={state.answers[state.current]}
              disabled={frozen}
              onSelect={(choice) => dispatch({ type: 'answer', index: state.current, choice })}
              onClear={() => dispatch({ type: 'clearAnswer', index: state.current })}
            />
          )}

          <div className={styles.controls}>
            <Button
              type="button"
              onClick={() => dispatch({ type: 'prev' })}
              disabled={state.current === 0}
            >
              Previous
            </Button>
            <Button
              type="button"
              aria-pressed={state.flags[state.current]}
              onClick={() => dispatch({ type: 'toggleFlag', index: state.current })}
              disabled={frozen}
            >
              {state.flags[state.current] ? 'Unflag' : 'Flag'}
            </Button>
            <Button
              type="button"
              onClick={() => dispatch({ type: 'next' })}
              disabled={state.current === state.numProblems - 1}
            >
              Next
            </Button>
            <Button
              type="button"
              variant="primary"
              className={styles.submit}
              onClick={triggerSubmit}
              disabled={frozen}
            >
              {state.phase === 'submitting' ? 'Submitting…' : 'Submit'}
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}
