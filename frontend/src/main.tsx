import { QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import 'katex/dist/katex.min.css'
import './styles/tokens.css'
import './index.css'
import App from './App'
import { AuthProvider } from '@/auth/AuthContext'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { configureApiClient } from '@/lib/api'
import { queryClient } from '@/lib/queryClient'

// Configure the generated client (same-origin base, send the session cookie)
// before any request is made.
configureApiClient()

const rootElement = document.getElementById('root')
if (rootElement === null) {
  throw new Error('Root element #root not found')
}

createRoot(rootElement).render(
  <StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  </StrictMode>
)
