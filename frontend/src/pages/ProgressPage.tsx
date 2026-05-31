/** The signed-in user's own progress dashboard. */
import { useQuery } from '@tanstack/react-query'
import { ErrorState, Spinner } from '@/components/States'
import { ProgressView } from '@/features/progress/ProgressView'
import { getMyProgress } from '@/lib/endpoints'
import { queryKeys } from '@/lib/queryClient'

export function ProgressPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.progress(),
    queryFn: getMyProgress,
  })

  return (
    <section>
      <h1>Your progress</h1>
      {isLoading && <Spinner label="Loading progress…" />}
      {isError && <ErrorState title="Could not load your progress" />}
      {data !== undefined && <ProgressView data={data} />}
    </section>
  )
}
