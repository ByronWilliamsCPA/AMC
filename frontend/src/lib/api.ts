/**
 * Configures the generated API client for the app's auth model.
 *
 * The backend uses an HTTP-only `amc_session` cookie (SameSite=Lax) and is
 * served same-origin behind a reverse proxy, so the client must:
 *  - use a same-origin base (never an absolute cross-origin URL, which would
 *    stop the cookie being sent). The generated SDK already encodes absolute
 *    paths like `/api/v1/...` and `/health/...`, so the base URL is the current
 *    origin (empty string), and
 *  - send credentials on every request so the browser attaches the cookie.
 *
 * The browser manages the cookie itself; we never read or store any session
 * material in JS (no localStorage), which is the whole point of the HTTP-only
 * design. There is therefore no `Authorization` header anywhere in the app.
 */
import { client } from '@/client'

/** Configure the singleton generated client. Call once at app startup. */
export function configureApiClient(): void {
  client.setConfig({
    // Same-origin: the SDK paths are already rooted at `/api/...` and
    // `/health/...`, so the base is just the current origin. The dev server
    // proxies those to the backend; production serves both behind one origin.
    baseUrl: '',
    // Attach the HTTP-only session cookie to every request.
    credentials: 'include',
  })
}

export { client }
