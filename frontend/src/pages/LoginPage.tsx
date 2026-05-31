/**
 * Login page. On success the session cookie is set by the server and the auth
 * context re-derives the user from `/auth/me`; we then return the user to where
 * they were headed.
 */
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/useAuth'
import { Button } from '@/components/ui/Button'
import { ApiError } from '@/lib/endpoints'
import styles from './LoginPage.module.css'

interface LocationState {
  from?: string
}

export function LoginPage() {
  const { user, loading, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user !== null) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login({ email, password })
      const dest = (location.state as LocationState | null)?.from ?? '/'
      navigate(dest, { replace: true })
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 401
          ? 'Invalid email or password.'
          : 'Could not sign in. Please try again.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>Sign in</h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        <label className={styles.label} htmlFor="email">
          Email
        </label>
        <input
          id="email"
          className={styles.input}
          type="email"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label className={styles.label} htmlFor="password">
          Password
        </label>
        <input
          id="password"
          className={styles.input}
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {error !== null && (
          <p role="alert" className={styles.error}>
            {error}
          </p>
        )}

        <Button
          type="submit"
          variant="primary"
          block
          className={styles.submit}
          disabled={submitting}
        >
          {submitting ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
      <p className={styles.footer}>
        Have an invite? <Link to="/register">Set up your account</Link>.
      </p>
    </main>
  )
}
