/**
 * Presentational progress dashboard, shared between "my progress" and the coach
 * view of a student (same `ProgressResponse` schema). Shows the synthesized
 * recommendation, the AMC unlocks, the algebra-gate warning, and the two
 * history tables (which collapse to cards on mobile via the Table primitive).
 */
import type { ProgressResponse } from '@/client'
import { EmptyState } from '@/components/States'
import { Alert, Badge, Table, type TableColumn, type TableRow } from '@/components/ui'
import styles from './ProgressView.module.css'

const CONTEST_COLUMNS: TableColumn[] = [
  { key: 'score', header: 'Score' },
  { key: 'correct', header: 'Correct' },
  { key: 'wrong', header: 'Wrong' },
  { key: 'blank', header: 'Blank' },
  { key: 'time', header: 'Time (s)' },
]

const DIAGNOSTIC_COLUMNS: TableColumn[] = [
  { key: 'instrument', header: 'Instrument' },
  { key: 'verdict', header: 'Verdict' },
  { key: 'result', header: 'Result' },
]

export function ProgressView({ data }: { data: ProgressResponse }) {
  const contestRows: TableRow[] = data.test_attempts.map((attempt) => {
    const a = attempt as Record<string, unknown>
    return {
      key: String(a.id),
      cells: {
        score: `${String(a.score)} / ${String(a.max_score)}`,
        correct: String(a.correct),
        wrong: String(a.wrong),
        blank: String(a.blank),
        time: String(a.time_used_sec),
      },
    }
  })

  const diagnosticRows: TableRow[] = data.diagnostic_attempts.map((attempt) => {
    const a = attempt as Record<string, unknown>
    const passed = Boolean(a.passed)
    return {
      key: String(a.id),
      cells: {
        instrument: String(a.instrument_id),
        verdict: <Badge tone={passed ? 'success' : 'warning'}>{String(a.verdict)}</Badge>,
        result: passed ? 'Passed' : 'Did not pass',
      },
    }
  })

  return (
    <div className={styles.progress}>
      <section className={styles.recommendation} aria-labelledby="rec-h">
        <h2 id="rec-h">Recommendation</h2>
        {data.recommendation_course ? (
          <p className={styles.course}>{data.recommendation_course}</p>
        ) : (
          <EmptyState>No recommendation yet.</EmptyState>
        )}
        <p>{data.recommendation_reason}</p>
        {data.algebra_warning && (
          <Alert severity="warning" role="status">
            {data.algebra_warning}
          </Alert>
        )}
        {(data.unlocked_by_amc ?? []).length > 0 && (
          <p>Your AMC score unlocks: {(data.unlocked_by_amc ?? []).join(', ')}.</p>
        )}
      </section>

      <section aria-labelledby="contests-h">
        <h2 id="contests-h">Contest history</h2>
        {contestRows.length === 0 ? (
          <EmptyState>No contests taken yet.</EmptyState>
        ) : (
          <Table caption="Contest history" columns={CONTEST_COLUMNS} rows={contestRows} />
        )}
      </section>

      <section aria-labelledby="diagnostics-h">
        <h2 id="diagnostics-h">Diagnostics</h2>
        {diagnosticRows.length === 0 ? (
          <EmptyState>No diagnostics taken yet.</EmptyState>
        ) : (
          <Table caption="Diagnostics" columns={DIAGNOSTIC_COLUMNS} rows={diagnosticRows} />
        )}
      </section>
    </div>
  )
}
