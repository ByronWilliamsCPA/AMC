/** Lists the placement diagnostics, linking each to its runner. */
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { EmptyState, ErrorState, Spinner } from '@/components/States'
import { listDiagnostics } from '@/lib/endpoints'
import { queryKeys } from '@/lib/queryClient'

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
        <ul className="diagnostic-list">
          {data.map((d) => (
            <li key={d.id}>
              <Link to={`/diagnostics/${d.id}`}>
                {d.course} — {d.kind}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
