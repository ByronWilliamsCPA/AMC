/**
 * App routing.
 *
 * Public routes (login, register) sit outside the auth guard; everything else is
 * wrapped in {@link RequireAuth}. The coach progress view is additionally
 * staff-only. Feature routes are lazy-loaded so the login bundle stays small
 * (the exam runner pulls in KaTeX, which is heavy).
 */
import { Suspense, lazy } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from '@/auth/RequireAuth'
import { Layout } from '@/components/Layout'
import { Spinner } from '@/components/States'

const ExamListPage = lazy(() =>
  import('@/pages/ExamListPage').then((m) => ({ default: m.ExamListPage }))
)
const ExamRunnerPage = lazy(() =>
  import('@/pages/ExamRunnerPage').then((m) => ({ default: m.ExamRunnerPage }))
)
const DiagnosticListPage = lazy(() =>
  import('@/pages/DiagnosticListPage').then((m) => ({
    default: m.DiagnosticListPage,
  }))
)
const DiagnosticRunnerPage = lazy(() =>
  import('@/pages/DiagnosticRunnerPage').then((m) => ({
    default: m.DiagnosticRunnerPage,
  }))
)
const ProgressPage = lazy(() =>
  import('@/pages/ProgressPage').then((m) => ({ default: m.ProgressPage }))
)
const UserProgressPage = lazy(() =>
  import('@/pages/UserProgressPage').then((m) => ({
    default: m.UserProgressPage,
  }))
)
const InvitePage = lazy(() => import('@/pages/InvitePage').then((m) => ({ default: m.InvitePage })))
const LoginPage = lazy(() => import('@/pages/LoginPage').then((m) => ({ default: m.LoginPage })))
const RegisterPage = lazy(() =>
  import('@/pages/RegisterPage').then((m) => ({ default: m.RegisterPage }))
)

function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/exams" replace />} />
          <Route path="exams" element={<ExamListPage />} />
          <Route path="exams/:examId" element={<ExamRunnerPage />} />
          <Route path="diagnostics" element={<DiagnosticListPage />} />
          <Route path="diagnostics/:instrumentId" element={<DiagnosticRunnerPage />} />
          <Route path="progress" element={<ProgressPage />} />
          <Route
            path="users/:userId/progress"
            element={
              <RequireAuth staffOnly>
                <UserProgressPage />
              </RequireAuth>
            }
          />
          <Route path="invite" element={<InvitePage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

export default App
