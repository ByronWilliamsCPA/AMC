/**
 * Authentication state derived from the server session.
 *
 * The session lives in an HTTP-only cookie the SPA cannot read, so "who am I"
 * comes from `GET /auth/me`. A 401 there is the *normal* logged-out signal, not
 * an error — the bootstrap must not redirect on it (that would loop on the
 * login page). `login`/`register`/`logout` just call the endpoints; the browser
 * manages the cookie, and we re-derive state from `/auth/me`.
 */
import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { LoginRequest, RegisterRequest, UserResponse } from '@/client'
import {
  ApiError,
  getMe,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
} from '@/lib/endpoints'

export interface AuthContextValue {
  /** The current user, or null when logged out. */
  user: UserResponse | null
  /** True until the initial `/auth/me` bootstrap resolves. */
  loading: boolean
  /** Whether the current user may act as staff (coach/admin). */
  isStaff: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (payload: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  /** Re-fetch `/auth/me` (e.g. after an out-of-band change). */
  refresh: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

const STAFF_ROLES = new Set(['coach', 'admin'])

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      setUser(await getMe())
    } catch (error) {
      // 401 is the expected "not logged in" answer; anything else we still
      // treat as unauthenticated for safety but surface via console.
      if (!(error instanceof ApiError) || error.status !== 401) {
        console.error('auth bootstrap failed', error)
      }
      setUser(null)
    }
  }, [])

  useEffect(() => {
    let active = true
    void (async () => {
      await refresh()
      if (active) setLoading(false)
    })()
    return () => {
      active = false
    }
  }, [refresh])

  const login = useCallback(
    async (credentials: LoginRequest) => {
      await loginRequest(credentials)
      await refresh()
    },
    [refresh]
  )

  const register = useCallback(
    async (payload: RegisterRequest) => {
      await registerRequest(payload)
      await refresh()
    },
    [refresh]
  )

  const logout = useCallback(async () => {
    await logoutRequest()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isStaff: user !== null && STAFF_ROLES.has(user.role),
      login,
      register,
      logout,
      refresh,
    }),
    [user, loading, login, register, logout, refresh]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
