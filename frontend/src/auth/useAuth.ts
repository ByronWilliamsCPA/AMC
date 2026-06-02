/** Hook to access the auth context. Separate file so AuthContext.tsx can be a
 * components-only module (keeps React Fast Refresh happy). */
import { useContext } from 'react'
import { AuthContext, type AuthContextValue } from '@/auth/AuthContext'

/** Access the auth context; throws if used outside an AuthProvider. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (ctx === null) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
