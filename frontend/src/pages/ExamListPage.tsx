/**
 * Lists available AMC papers, optionally filtered by contest, linking each to
 * the runner.
 */
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { EmptyState, ErrorState, Spinner } from '@/components/States'
import { listExams } from '@/lib/endpoints'
import { queryKeys } from '@/lib/queryClient'

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

      <div className="filter-bar" role="group" aria-label="Filter by contest">
        <button
          type="button"
          aria-pressed={contest === undefined}
          onClick={() => setContest(undefined)}
        >
          All
        </button>
        {CONTESTS.map((c) => (
          <button key={c} type="button" aria-pressed={contest === c} onClick={() => setContest(c)}>
            {c}
          </button>
        ))}
      </div>

      {isLoading && <Spinner label="Loading tests…" />}
      {isError && <ErrorState title="Could not load tests" />}
      {data !== undefined && data.length === 0 && <EmptyState>No tests available yet.</EmptyState>}
      {data !== undefined && data.length > 0 && (
        <ul className="exam-list">
          {data.map((exam) => (
            <li key={exam.id}>
              <Link to={`/exams/${exam.id}`}>
                {exam.contest} {exam.year}
                {exam.variant ? exam.variant : ''} — {exam.num_problems} problems
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
