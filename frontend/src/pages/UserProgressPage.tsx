/** Coach/admin view of a specific student's progress (staff-only route). */
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { ErrorState, Spinner } from '@/components/States'
import { ProgressView } from '@/features/progress/ProgressView'
import { getUserProgress } from '@/lib/endpoints'
import { queryKeys } from '@/lib/queryClient'

export function UserProgressPage() {
  const { userId = '' } = useParams()
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.userProgress(userId),
    queryFn: () => getUserProgress(userId),
  })

  return (
    <section>
      <h1>Student progress</h1>
      {isLoading && <Spinner label="Loading progress…" />}
      {isError && <ErrorState title="Could not load this student's progress" />}
      {data !== undefined && <ProgressView data={data} />}
    </section>
  )
}
