/**
 * Post-submission review: the only place the answer key is shown. Renders the
 * server-graded `ExamResultResponse` (score breakdown + per-problem outcome).
 */
import type { ExamResultResponse } from '@/client'

export function ExamReview({ result }: { result: ExamResultResponse }) {
  return (
    <section className="review" aria-live="polite">
      <h2>Your result</h2>
      <dl className="review__score">
        <div>
          <dt>Score</dt>
          <dd>
            {result.score} / {result.max_score}
          </dd>
        </div>
        <div>
          <dt>Correct</dt>
          <dd>{result.correct}</dd>
        </div>
        <div>
          <dt>Wrong</dt>
          <dd>{result.wrong}</dd>
        </div>
        <div>
          <dt>Blank</dt>
          <dd>{result.blank}</dd>
        </div>
      </dl>

      <table className="review__table">
        <caption>Per-problem review</caption>
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Your answer</th>
            <th scope="col">Correct</th>
            <th scope="col">Outcome</th>
          </tr>
        </thead>
        <tbody>
          {result.review.map((item) => (
            <tr key={item.n}>
              <td>{item.n}</td>
              <td>{item.your ?? '—'}</td>
              <td>{item.correct}</td>
              <td>{outcome(item.voided, item.ok)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

function outcome(voided: boolean, ok: boolean): string {
  if (voided) return 'Void'
  return ok ? 'Correct' : 'Incorrect'
}
