import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { LoginPage } from '@/pages/LoginPage'
import { renderWithProviders } from '@/test/renderWithProviders'

describe('LoginPage', () => {
  it('shows an error on bad credentials (no cookie set)', async () => {
    renderWithProviders(<LoginPage />, { route: '/login' })

    await userEvent.type(screen.getByLabelText('Email'), 'student@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'wrong-password')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/invalid email or password/i)
    })
  })

  it('shows no error when the login call succeeds', async () => {
    renderWithProviders(<LoginPage />, { route: '/login' })

    await userEvent.type(screen.getByLabelText('Email'), 'student@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'correct-password')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    // Let the submit settle, then assert the credential error never appeared.
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /sign in/i })).not.toBeDisabled()
    })
    expect(screen.queryByText(/invalid email or password/i)).not.toBeInTheDocument()
  })
})
