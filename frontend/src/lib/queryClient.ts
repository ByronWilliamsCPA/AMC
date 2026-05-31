/**
 * Shared TanStack Query client.
 *
 * Server reads (catalog, exam detail, progress) flow through Query so each
 * screen gets caching, `isLoading`/`isError`, and invalidation for free. A 401
 * from a protected query is surfaced to the route guard rather than retried, so
 * an expired session sends the user to login promptly.
 */
import { QueryClient } from '@tanstack/react-query'
import { ApiError } from '@/lib/endpoints'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Don't hammer the API on auth failures; let the guard handle 401/403.
      retry: (failureCount, error) => {
        if (
          error instanceof ApiError &&
          (error.status === 401 || error.status === 403 || error.status === 404)
        ) {
          return false
        }
        return failureCount < 2
      },
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
})

/** Query keys, centralised so invalidation is consistent. */
export const queryKeys = {
  exams: (contest?: string) => ['exams', contest ?? 'all'] as const,
  exam: (id: string) => ['exam', id] as const,
  diagnostics: () => ['diagnostics'] as const,
  diagnostic: (id: string) => ['diagnostic', id] as const,
  progress: () => ['progress'] as const,
  userProgress: (id: string) => ['progress', id] as const,
}
