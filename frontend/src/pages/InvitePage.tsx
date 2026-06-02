/**
 * Staff-only: mint a one-time invite. The raw token is shown exactly once for
 * the coach to share (the server stores only its hash), with a copy button.
 */
import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import type { InviteCreatedResponse } from '@/client'
import { Alert, Button, Card, Select, TextField } from '@/components/ui'
import { createInvite } from '@/lib/endpoints'
import styles from './InvitePage.module.css'

const ROLE_OPTIONS = [
  { value: 'student', label: 'student' },
  { value: 'coach', label: 'coach' },
  { value: 'admin', label: 'admin' },
]

export function InvitePage() {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<string>('student')
  const [created, setCreated] = useState<InviteCreatedResponse | null>(null)
  const [copied, setCopied] = useState(false)

  const mutation = useMutation({
    mutationFn: () => createInvite({ email, role }),
    onSuccess: (invite) => setCreated(invite),
  })

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    setCreated(null)
    setCopied(false)
    mutation.mutate()
  }

  const inviteLink =
    created !== null ? `${window.location.origin}/register?token=${created.token}` : null

  const handleCopy = () => {
    if (inviteLink === null) return
    void navigator.clipboard.writeText(inviteLink).then(() => setCopied(true))
  }

  return (
    <section className={styles.page}>
      <h1>Invite a student</h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        <TextField
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Select
          label="Role"
          options={ROLE_OPTIONS}
          value={role}
          onChange={(e) => setRole(e.target.value)}
        />
        <Button type="submit" variant="primary" disabled={mutation.isPending}>
          {mutation.isPending ? 'Creating…' : 'Create invite'}
        </Button>
        {mutation.isError && <Alert severity="error">Could not create the invite.</Alert>}
      </form>

      {created !== null && inviteLink !== null && (
        <Card as="div" aria-live="polite">
          <h2 className={styles.resultHeading}>Share this link once</h2>
          <p>
            Send this to <strong>{created.email}</strong>. It won&apos;t be shown again.
          </p>
          <div className={styles.linkRow}>
            <code className={styles.link}>{inviteLink}</code>
            <Button type="button" onClick={handleCopy}>
              {copied ? 'Copied' : 'Copy'}
            </Button>
          </div>
        </Card>
      )}
    </section>
  )
}
