/**
 * Route guard: gates protected routes on the `/auth/me`-derived session.
 *
 * While the initial bootstrap is in flight it shows a spinner; once resolved,
 * an unauthenticated user is redirected to `/login` (preserving where they were
 * headed), and a non-staff user hitting a staff-only route is sent home.
 */
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/auth/useAuth'
import { Spinner } from '@/components/States'

export function RequireAuth({
  children,
  staffOnly = false,
}: {
  children: ReactNode
  staffOnly?: boolean
}) {
  const { user, loading, isStaff } = useAuth()
  const location = useLocation()

  if (loading) {
    return <Spinner label="Checking your session…" />
  }
  if (user === null) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  if (staffOnly && !isStaff) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}
