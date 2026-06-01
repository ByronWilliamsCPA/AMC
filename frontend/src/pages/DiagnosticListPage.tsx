/** Lists the placement diagnostics, linking each to its runner. */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { EmptyState, ErrorState, Spinner } from '@/components/States'
import { Card } from '@/components/ui'
import { listDiagnostics } from '@/lib/endpoints'
import { queryKeys } from '@/lib/queryClient'
import styles from './DiagnosticListPage.module.css'

export function DiagnosticListPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.diagnostics(),
    queryFn: listDiagnostics,
  })

  return (
    <section>
      <h1>Placement diagnostics</h1>
      {isLoading && <Spinner label="Loading diagnostics…" />}
      {isError && <ErrorState title="Could not load diagnostics" />}
      {data !== undefined && data.length === 0 && (
        <EmptyState>No diagnostics available yet.</EmptyState>
      )}
      {data !== undefined && data.length > 0 && (
        <ul className={styles.list}>
          {data.map((d) => (
            <Card as="li" interactive key={d.id}>
              <Link to={`/diagnostics/${d.id}`} className={styles.link}>
                {d.course} <span className={styles.meta}>- {d.kind}</span>
              </Link>
            </Card>
          ))}
        </ul>
      )}
    </section>
  )
}
