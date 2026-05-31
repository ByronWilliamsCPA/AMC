/**
 * Staff-only: mint a one-time invite. The raw token is shown exactly once for
 * the coach to share (the server stores only its hash).
 */
import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import type { InviteCreatedResponse } from '@/client'
import { ErrorState } from '@/components/States'
import { createInvite } from '@/lib/endpoints'

const ROLES = ['student', 'coach', 'admin'] as const

export function InvitePage() {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<string>('student')
  const [created, setCreated] = useState<InviteCreatedResponse | null>(null)

  const mutation = useMutation({
    mutationFn: () => createInvite({ email, role }),
    onSuccess: (invite) => setCreated(invite),
  })

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    setCreated(null)
    mutation.mutate()
  }

  const inviteLink =
    created !== null ? `${window.location.origin}/register?token=${created.token}` : null

  return (
    <section>
      <h1>Invite a student</h1>
      <form onSubmit={handleSubmit} className="auth-form">
        <label htmlFor="invite_email">Email</label>
        <input
          id="invite_email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label htmlFor="invite_role">Role</label>
        <select id="invite_role" value={role} onChange={(e) => setRole(e.target.value)}>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>

        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Creating…' : 'Create invite'}
        </button>
        {mutation.isError && <ErrorState title="Could not create the invite." />}
      </form>

      {created !== null && inviteLink !== null && (
        <div className="invite-result" aria-live="polite">
          <h2>Share this link once</h2>
          <p>
            Send this to <strong>{created.email}</strong>. It won&apos;t be shown again.
          </p>
          <code className="invite-link">{inviteLink}</code>
        </div>
      )}
    </section>
  )
}
