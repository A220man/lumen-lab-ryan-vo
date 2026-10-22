// Login page
import { useAuth } from '../auth/useAuth'

export function LoginPage() {
  const { login, loading } = useAuth()

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f5f5f5',
    }}>
      <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <h1 style={{ marginBottom: '0.5rem' }}>Lumen Lab</h1>
          <p style={{ color: '#6b7280' }}>Sign in to continue</p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <button
            className="btn btn-primary"
            onClick={login}
            disabled={loading}
            style={{ padding: '0.75rem 1.5rem' }}
          >
            {loading ? (
              <>
                <div className="spinner" /> Signing in...
              </>
            ) : (
              'Sign in with Keycloak'
            )}
          </button>
        </div>

        <p style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.75rem', color: '#9ca3af' }}>
          Demo mode: authentication not yet implemented
        </p>
      </div>
    </div>
  )
}