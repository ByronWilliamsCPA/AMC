/**
 * Presentational progress dashboard, shared between "my progress" and the coach
 * view of a student (same `ProgressResponse` schema). Shows the synthesized
 * recommendation, the AMC unlocks, the algebra-gate warning, and the two
 * history tables.
 */
import type { ProgressResponse } from '@/client'
import { EmptyState } from '@/components/States'

export function ProgressView({ data }: { data: ProgressResponse }) {
  return (
    <div className="progress">
      <section className="progress__recommendation" aria-labelledby="rec-h">
        <h2 id="rec-h">Recommendation</h2>
        {data.recommendation_course ? (
          <p className="progress__course">{data.recommendation_course}</p>
        ) : (
          <EmptyState>No recommendation yet.</EmptyState>
        )}
        <p>{data.recommendation_reason}</p>
        {data.algebra_warning && (
          <p role="alert" className="progress__warning">
            {data.algebra_warning}
          </p>
        )}
        {(data.unlocked_by_amc ?? []).length > 0 && (
          <p>Your AMC score unlocks: {(data.unlocked_by_amc ?? []).join(', ')}.</p>
        )}
      </section>

      <section aria-labelledby="contests-h">
        <h2 id="contests-h">Contest history</h2>
        {data.test_attempts.length === 0 ? (
          <EmptyState>No contests taken yet.</EmptyState>
        ) : (
          <table className="progress__table">
            <thead>
              <tr>
                <th scope="col">Score</th>
                <th scope="col">Correct</th>
                <th scope="col">Wrong</th>
                <th scope="col">Blank</th>
                <th scope="col">Time (s)</th>
              </tr>
            </thead>
            <tbody>
              {data.test_attempts.map((attempt) => {
                const a = attempt as Record<string, unknown>
                return (
                  <tr key={String(a.id)}>
                    <td>
                      {String(a.score)} / {String(a.max_score)}
                    </td>
                    <td>{String(a.correct)}</td>
                    <td>{String(a.wrong)}</td>
                    <td>{String(a.blank)}</td>
                    <td>{String(a.time_used_sec)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </section>

      <section aria-labelledby="diagnostics-h">
        <h2 id="diagnostics-h">Diagnostics</h2>
        {data.diagnostic_attempts.length === 0 ? (
          <EmptyState>No diagnostics taken yet.</EmptyState>
        ) : (
          <table className="progress__table">
            <thead>
              <tr>
                <th scope="col">Instrument</th>
                <th scope="col">Verdict</th>
                <th scope="col">Result</th>
              </tr>
            </thead>
            <tbody>
              {data.diagnostic_attempts.map((attempt) => {
                const a = attempt as Record<string, unknown>
                return (
                  <tr key={String(a.id)}>
                    <td>{String(a.instrument_id)}</td>
                    <td>{String(a.verdict)}</td>
                    <td>{a.passed ? 'Passed' : 'Did not pass'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}
