import '@testing-library/jest-dom'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { client } from '@/client'
import { server } from '@/test/server'

// In jsdom, node's fetch cannot build a Request from a relative URL, so point
// the client at the jsdom origin (absolute). The app uses an empty base in the
// browser, where relative URLs resolve fine; behaviour (credentials, same
// host) is otherwise identical. MSW handlers use `*/path` so they still match.
client.setConfig({
  baseUrl: 'http://localhost:3000',
  credentials: 'include',
})

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
