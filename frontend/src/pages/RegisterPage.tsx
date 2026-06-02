/**
 * Invite redemption page. Reads the invite token from `?token=…`, validates it
 * for display, and on submit creates the account (server sets the session) and
 * re-derives auth state.
 */
import { useEffect, useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/auth/useAuth'
import { Alert, Button, TextField } from '@/components/ui'
import { ApiError, validateInvite } from '@/lib/endpoints'
import styles from './RegisterPage.module.css'

export function RegisterPage() {
  const { user, loading, register } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''

  const [inviteEmail, setInviteEmail] = useState<string | null>(null)
  const [inviteValid, setInviteValid] = useState<boolean | null>(null)
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (token === '') {
      setInviteValid(false)
      return
    }
    let active = true
    void (async () => {
      try {
        const result = await validateInvite(token)
        if (!active) return
        setInviteValid(result.valid)
        setInviteEmail(result.email ?? null)
      } catch {
        if (active) setInviteValid(false)
      }
    })()
    return () => {
      active = false
    }
  }, [token])

  if (!loading && user !== null) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await register({ token, display_name: displayName, password })
      navigate('/', { replace: true })
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 422
          ? 'Password must be at least 8 characters.'
          : 'Could not create your account. The invite may be invalid or used.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className={styles.page}>
      <h1>Set up your account</h1>
      {inviteValid === false && (
        <Alert severity="error">
          This invite link is invalid or has expired. Ask your coach for a new one.
        </Alert>
      )}
      {inviteValid === true && (
        <form onSubmit={handleSubmit} className={styles.form}>
          {inviteEmail !== null && (
            <p>
              Creating an account for <strong>{inviteEmail}</strong>.
            </p>
          )}
          <TextField
            label="Display name"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
          />
          <TextField
            label="Password"
            hint="8+ characters"
            type="password"
            autoComplete="new-password"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error !== null && <Alert severity="error">{error}</Alert>}

          <Button type="submit" variant="primary" block disabled={submitting}>
            {submitting ? 'Creating…' : 'Create account'}
          </Button>
        </form>
      )}
      <p className={styles.footer}>
        Already set up? <Link to="/login">Sign in</Link>.
      </p>
    </main>
  )
}
