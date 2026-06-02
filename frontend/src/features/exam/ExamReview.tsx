/**
 * Post-submission review: the only place the answer key is shown. Renders the
 * server-graded `ExamResultResponse` (score breakdown + per-problem outcome).
 * The per-problem table collapses to cards on mobile via the Table primitive.
 */
import type { ReactNode } from 'react'
import type { ExamResultResponse } from '@/client'
import { Badge, Table, type TableColumn, type TableRow } from '@/components/ui'
import styles from './ExamReview.module.css'

const COLUMNS: TableColumn[] = [
  { key: 'n', header: '#' },
  { key: 'your', header: 'Your answer' },
  { key: 'correct', header: 'Correct' },
  { key: 'outcome', header: 'Outcome' },
]

function outcome(voided: boolean, ok: boolean): ReactNode {
  if (voided) return <Badge tone="neutral">Void</Badge>
  return ok ? <Badge tone="success">Correct</Badge> : <Badge tone="danger">Incorrect</Badge>
}

export function ExamReview({ result }: { result: ExamResultResponse }) {
  const rows: TableRow[] = result.review.map((item) => ({
    key: String(item.n),
    cells: {
      n: item.n,
      your: item.your ?? '-',
      correct: item.correct,
      outcome: outcome(item.voided, item.ok),
    },
  }))

  return (
    <section className={styles.review} aria-live="polite">
      <h2>Your result</h2>
      <dl className={styles.score}>
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

      <Table caption="Per-problem review" columns={COLUMNS} rows={rows} />
    </section>
  )
}
