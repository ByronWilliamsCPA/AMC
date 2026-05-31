/**
 * App shell: a skip link, role-aware header nav, and the routed content via
 * Outlet. On navigation, focus moves to the main landmark and the new section
 * is announced in a polite live region, so keyboard and screen-reader users
 * aren't stranded on the old (now unmounted) control.
 */
import { useEffect, useRef } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/auth/useAuth'
import { Button } from '@/components/ui/Button'
import styles from './Layout.module.css'

/** Best-effort label for the current section, for the route announcer. */
function sectionLabel(pathname: string): string {
  const segment = pathname.split('/')[1] ?? ''
  const labels: Record<string, string> = {
    exams: 'Practice tests',
    diagnostics: 'Diagnostics',
    progress: 'Progress',
    invite: 'Invite a student',
    users: 'Student progress',
  }
  return labels[segment] ?? 'AMC Trainer'
}

export function Layout() {
  const { user, isStaff, logout } = useAuth()
  const location = useLocation()
  const mainRef = useRef<HTMLElement>(null)
  const firstRender = useRef(true)

  // Move focus to <main> on navigation (but not on the initial mount, so we
  // don't steal focus on first load).
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false
      return
    }
    mainRef.current?.focus()
  }, [location.pathname])

  return (
    <div className={styles.layout}>
      <a className={styles.skipLink} href="#main-content">
        Skip to main content
      </a>
      <header className={styles.header}>
        <NavLink to="/" className={styles.brand}>
          AMC Trainer
        </NavLink>
        <nav className={styles.nav} aria-label="Primary">
          <NavLink to="/exams">Tests</NavLink>
          <NavLink to="/diagnostics">Diagnostics</NavLink>
          <NavLink to="/progress">Progress</NavLink>
          {isStaff && <NavLink to="/invite">Invite</NavLink>}
        </nav>
        <div className={styles.user}>
          {user !== null && (
            <>
              <span className={styles.userName}>{user.display_name}</span>
              <Button type="button" onClick={() => void logout()}>
                Sign out
              </Button>
            </>
          )}
        </div>
      </header>
      <main id="main-content" className={styles.main} tabIndex={-1} ref={mainRef}>
        <Outlet />
      </main>
      {/* Route announcer: names the new section for screen-reader users. */}
      <div aria-live="polite" className="visually-hidden">
        {sectionLabel(location.pathname)}
      </div>
    </div>
  )
}
