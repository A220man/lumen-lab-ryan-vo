// Sandbox dashboard component
import { useState, useEffect } from 'react'
import { api } from '../api/client'

interface Sandbox {
  id: string
  name: string
  image: string
  arch: string
  status: 'pending' | 'building' | 'running' | 'stopped' | 'error'
  created_at: string
}

export function SandboxDashboard() {
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

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/api/v1/sandboxes/${id}`)
      setSandboxes(prev => prev.filter(s => s.id !== id))
    } catch (err) {
      setError('Failed to delete sandbox')
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

  if (sandboxes.length === 0) {
    return (
      <div className="card empty-state">
        <div className="empty-state-icon">📦</div>
        <h3>No sandboxes yet</h3>
        <p>Create a sandbox environment for cross-OS testing.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>Sandbox Environments</h1>

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
                <th></th>
              </tr>
            </thead>
            <tbody>
              {sandboxes.map(s => (
                <tr key={s.id}>
                  <td>{s.id.slice(0, 8)}...</td>
                  <td>{s.name}</td>
                  <td>{s.image}</td>
                  <td>{s.arch}</td>
                  <td>
                    <span className={`badge badge-${s.status === 'running' ? 'success' : s.status === 'error' ? 'error' : 'warning'}`}>
                      {s.status}
                    </span>
                  </td>
                  <td>{new Date(s.created_at).toLocaleString()}</td>
                  <td>
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => handleDelete(s.id)}
                      disabled={s.status === 'running'}
                    >
                      {s.status === 'running' ? 'Running' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
