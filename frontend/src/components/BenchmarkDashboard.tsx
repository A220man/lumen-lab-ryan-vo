// Benchmark dashboard component
import { useState, useEffect } from 'react'
import { api } from '../api/client'

interface Benchmark {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'cancelled'
  created_at: string
  max_latency_ms?: number | null
  avg_latency_ms?: number | null
}

export function BenchmarkDashboard() {
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchBenchmarks()
  }, [])

  const fetchBenchmarks = async () => {
    try {
      setLoading(true)
      const data = await api.get<{ items: Benchmark[] }>('/api/v1/benchmarks')
      setBenchmarks(data.items || [])
    } catch (err) {
      setError('Failed to load benchmarks')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async (id: string) => {
    try {
      await api.post<Benchmark>(`/api/v1/benchmarks/${id}/cancel`)
      setBenchmarks(prev => prev.filter(b => b.id !== id))
    } catch (err) {
      setError('Failed to cancel benchmark')
    }
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '3rem' }}><div className="spinner" /></div>
  }

  if (error) {
    return (
      <div className="card">
        <p className="badge badge-error">{error}</p>
        <button className="btn btn-primary" onClick={fetchBenchmarks}>Retry</button>
      </div>
    )
  }

  if (benchmarks.length === 0) {
    return (
      <div className="card empty-state">
        <div className="empty-state-icon">⚡</div>
        <h3>No benchmarks yet</h3>
        <p>Create a new benchmark run to get started.</p>
      </div>
    )
  }

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>Benchmark Runs</h1>

      <div className="card">
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Status</th>
                <th>Created</th>
                <th>Max Latency</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {benchmarks.map(b => (
                <tr key={b.id}>
                  <td>{b.id.slice(0, 8)}...</td>
                  <td>{b.name}</td>
                  <td>
                    <span className={`badge badge-${b.status}`}>
                      {b.status}
                    </span>
                  </td>
                  <td>{new Date(b.created_at).toLocaleString()}</td>
                  <td>{b.max_latency_ms ?? '—'}</td>
                  <td>
                    <button
                      className="btn btn-sm btn-danger"
                      onClick={() => handleCancel(b.id)}
                      disabled={b.status !== 'running'}
                    >
                      {b.status === 'running' ? 'Cancel' : 'N/A'}
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
