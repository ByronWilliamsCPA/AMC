/**
 * Lists available AMC papers, optionally filtered by contest, linking each to
 * the runner.
 */
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState, ErrorState, Spinner } from '@/components/States'
import { Button, Card } from '@/components/ui'
import { listExams } from '@/lib/endpoints'
import { queryKeys } from '@/lib/queryClient'
import styles from './ExamListPage.module.css'

const CONTESTS = ['AMC 8', 'AMC 10', 'AMC 12'] as const

export function ExamListPage() {
  const [contest, setContest] = useState<string | undefined>(undefined)
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.exams(contest),
    queryFn: () => listExams(contest),
  })

  return (
    <section>
      <h1>Practice tests</h1>

      <div className={styles.filterBar} role="group" aria-label="Filter by contest">
        <Button
          type="button"
          className={styles.filter}
          aria-pressed={contest === undefined}
          onClick={() => setContest(undefined)}
        >
          All
        </Button>
        {CONTESTS.map((c) => (
          <Button
            key={c}
            type="button"
            className={styles.filter}
            aria-pressed={contest === c}
            onClick={() => setContest(c)}
          >
            {c}
          </Button>
        ))}
      </div>

      {isLoading && <Spinner label="Loading tests…" />}
      {isError && <ErrorState title="Could not load tests" />}
      {data !== undefined && data.length === 0 && <EmptyState>No tests available yet.</EmptyState>}
      {data !== undefined && data.length > 0 && (
        <ul className={styles.list}>
          {data.map((exam) => (
            <Card as="li" interactive key={exam.id}>
              <Link to={`/exams/${exam.id}`} className={styles.link}>
                {exam.contest} {exam.year}
                {exam.variant ? exam.variant : ''}{' '}
                <span className={styles.meta}>- {exam.num_problems} problems</span>
              </Link>
            </Card>
          ))}
        </ul>
      )}
    </section>
  )
}
