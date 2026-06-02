/**
 * Mock Service Worker server for component tests, so screens that call the
 * generated client run without a real backend.
 */
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

const STUDENT = {
  id: '11111111-1111-1111-1111-111111111111',
  email: 'student@example.com',
  display_name: 'Student',
  role: 'student',
}

// Host-agnostic patterns (`*/path`) so they match the relative same-origin URLs
// the client issues regardless of the jsdom origin.
export const handlers = [
  // Default: logged out.
  http.get('*/api/v1/auth/me', () =>
    HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
  ),
  http.post('*/api/v1/auth/login', async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string }
    if (body.password === 'correct-password') {
      return HttpResponse.json(STUDENT, { status: 200 })
    }
    return HttpResponse.json(
      { error: 'AuthenticationError', message: 'Invalid email or password' },
      { status: 401 }
    )
  }),
  http.post('*/api/v1/auth/logout', () => new HttpResponse(null, { status: 204 })),
]

export const server = setupServer(...handlers)
export { STUDENT }
