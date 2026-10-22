// Layout component with navigation
import { Outlet, Link, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

export function Layout() {
  const location = useLocation()
  const { logout, user } = useAuth()

  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/benchmarks', label: 'Benchmarks' },
    { path: '/sandboxes', label: 'Sandboxes' },
    { path: '/hyprland', label: 'Hyprland' },
  ]

  const handleLogout = async () => {
    await logout()
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        background: 'white',
        borderBottom: '1px solid #e5e7eb',
        padding: '0 1.5rem',
        height: '64px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 10,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <Link to="/" style={{ fontWeight: 700, fontSize: '1.25rem', color: '#1a1a1a' }}>
            Lumen Lab
          </Link>
          <nav style={{ display: 'flex', gap: '0.5rem' }}>
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  fontWeight: 500,
                  fontSize: '0.875rem',
                  color: location.pathname === item.path ? '#2563eb' : '#6b7280',
                  backgroundColor: location.pathname === item.path ? '#eff6ff' : 'transparent',
                }}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
            {user?.preferred_username || user?.email || 'User'}
          </span>
          <button onClick={handleLogout} className="btn btn-secondary" style={{ fontSize: '0.875rem' }}>
            Logout
          </button>
        </div>
      </header>
      <main style={{ flex: 1, padding: '1.5rem' }}>
        <div className="container">
          <Outlet />
        </div>
      </main>
      <footer style={{
        background: 'white',
        borderTop: '1px solid #e5e7eb',
        padding: '1rem 1.5rem',
        textAlign: 'center',
        fontSize: '0.75rem',
        color: '#9ca3af',
      }}>
          {'Lumen Lab \u2014 Ryan Vo <ryandtvo@gmail.com> \u2014 AI & Machine Learning'}
      </footer>
    </div>
  )
}