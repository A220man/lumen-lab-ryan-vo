// Sandboxes page - placeholder
import { useState, useEffect } from 'react'
import { api } from '../api/client'

interface Sandbox {
  id: string
  name: string
  image: string
  arch: string
  status: string
  created_at: string
}

export function SandboxesPage() {
  const [sandboxes, setSandboxes] = useState<Sandbox[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSandboxes()
  }, [])

  const fetchSandboxes = async () => {
    try {
      setLoading(true)
      const data = await api.get<{ items: Sandbox[] }>('/api/v1/sandboxes')
      setSandboxes(data.items || [])
    } catch (err) {
      setError('Failed to load sandboxes')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem' }}><div className="spinner" /></div>
  }

  if (error) {
    return (
      <div className="card">
        <p className="badge badge-error">{error}</p>
        <button className="btn btn-primary" onClick={fetchSandboxes}>Retry</button>
      </div>
    )
  }

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>Sandboxes</h1>

      {sandboxes.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-state-icon">📦</div>
          <h3>No sandboxes yet</h3>
          <p>Create a sandbox environment for cross-OS testing.</p>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Image</th>
                  <th>Arch</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {sandboxes.map(s => (
                  <tr key={s.id}>
                    <td>{s.id.slice(0, 8)}...</td>
                    <td>{s.name}</td>
                    <td>{s.image}</td>
                    <td>{s.arch}</td>
                    <td><span className={`badge badge-${s.status === 'running' ? 'success' : 'warning'}`}>{s.status}</span></td>
                    <td>{new Date(s.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}