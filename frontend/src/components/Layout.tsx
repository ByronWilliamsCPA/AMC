/** App shell: header nav (role-aware) plus the routed content via Outlet. */
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '@/auth/useAuth'

export function Layout() {
  const { user, isStaff, logout } = useAuth()

  return (
    <div className="layout">
      <header className="layout__header">
        <NavLink to="/" className="layout__brand">
          AMC Trainer
        </NavLink>
        <nav className="layout__nav" aria-label="Primary">
          <NavLink to="/exams">Tests</NavLink>
          <NavLink to="/diagnostics">Diagnostics</NavLink>
          <NavLink to="/progress">Progress</NavLink>
          {isStaff && <NavLink to="/invite">Invite</NavLink>}
        </nav>
        <div className="layout__user">
          {user !== null && (
            <>
              <span>{user.display_name}</span>
              <button type="button" onClick={() => void logout()}>
                Sign out
              </button>
            </>
          )}
        </div>
      </header>
      <main className="layout__main">
        <Outlet />
      </main>
    </div>
  )
}
