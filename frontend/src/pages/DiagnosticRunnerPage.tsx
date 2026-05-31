/**
 * Diagnostic runner (US-003 input side).
 *
 * Auto-graded items take a typed answer; manual (symbolic) items are answered
 * on paper and self-marked here. Submitting posts `{responses, marks,
 * elapsed_sec}`; the server grades (auto items server-side, manual via the
 * self-marks) and returns the verdict, which is the only place the answer is
 * revealed.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Tex } from '@/components/Tex'
import { ErrorState, Spinner } from '@/components/States'
import type { DiagnosticDetail, DiagnosticResultResponse } from '@/client'
import { getDiagnostic, submitDiagnostic } from '@/lib/endpoints'
import { queryKeys } from '@/lib/queryClient'

export function DiagnosticRunnerPage() {
  const { instrumentId = '' } = useParams()
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.diagnostic(instrumentId),
    queryFn: () => getDiagnostic(instrumentId),
  })

  if (isLoading) return <Spinner label="Loading diagnostic…" />
  if (isError || data === undefined) return <ErrorState title="Could not load this diagnostic" />

  return <DiagnosticInner instrument={data} />
}

function DiagnosticInner({ instrument }: { instrument: DiagnosticDetail }) {
  const queryClient = useQueryClient()
  const startedAtRef = useRef(Date.now())
  const [responses, setResponses] = useState<Record<string, string>>({})
  const [marks, setMarks] = useState<Record<string, boolean>>({})
  const [result, setResult] = useState<DiagnosticResultResponse | null>(null)

  const submitMutation = useMutation({
    mutationFn: () =>
      submitDiagnostic(instrument.id, {
        responses,
        marks,
        elapsed_sec: Math.round((Date.now() - startedAtRef.current) / 1000),
      }),
    onSuccess: (graded) => {
      setResult(graded)
      void queryClient.invalidateQueries({ queryKey: queryKeys.progress() })
    },
  })

  if (result !== null) {
    return (
      <section className="diagnostic-result" aria-live="polite">
        <h1>{instrument.course} — result</h1>
        <p>
          <strong>{result.verdict.toUpperCase()}</strong> — {result.summary}
        </p>
        <p>
          {result.correct} of {result.total} correct. {result.passed ? 'Passed.' : 'Did not pass.'}
        </p>
      </section>
    )
  }

  return (
    <section className="diagnostic">
      <h1>{instrument.course}</h1>
      <p className="diagnostic__instructions">{instrument.instructions}</p>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          submitMutation.mutate()
        }}
      >
        <ol className="diagnostic__items">
          {instrument.items.map((item) => (
            <li key={item.id} className="diagnostic__item">
              <p className="diagnostic__prompt">
                <span className="diagnostic__label">{item.label}.</span> <Tex tex={item.prompt} />
              </p>

              {item.manual ? (
                <label className="diagnostic__selfmark">
                  <input
                    type="checkbox"
                    checked={marks[item.id] ?? false}
                    onChange={(e) =>
                      setMarks((prev) => ({
                        ...prev,
                        [item.id]: e.target.checked,
                      }))
                    }
                  />
                  I solved this correctly (self-marked)
                </label>
              ) : (
                <label className="diagnostic__answer">
                  <span className="visually-hidden">Answer for {item.label}</span>
                  <input
                    type="text"
                    value={responses[item.id] ?? ''}
                    onChange={(e) =>
                      setResponses((prev) => ({
                        ...prev,
                        [item.id]: e.target.value,
                      }))
                    }
                    aria-label={`Answer for ${item.label}`}
                  />
                </label>
              )}
            </li>
          ))}
        </ol>

        <button type="submit" disabled={submitMutation.isPending}>
          {submitMutation.isPending ? 'Submitting…' : 'Submit diagnostic'}
        </button>
        {submitMutation.isError && <ErrorState title="Could not submit. Please try again." />}
      </form>
    </section>
  )
}
