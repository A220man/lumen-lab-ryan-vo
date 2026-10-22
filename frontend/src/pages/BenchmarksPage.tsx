// Benchmarks page - placeholder
import { useState, useEffect } from 'react'
import { api } from '../api/client'

interface Benchmark {
  id: string
  name: string
  status: string
  created_at: string
}

export function BenchmarksPage() {
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

  const handleRunBenchmark = async () => {
    try {
      await api.post('/api/v1/benchmarks', { name: 'New Benchmark' })
      fetchBenchmarks()
    } catch (err) {
      setError('Failed to create benchmark')
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

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1>Benchmarks</h1>
        <button className="btn btn-primary" onClick={handleRunBenchmark} disabled={loading}>
          Run Benchmark
        </button>
      </div>

      {benchmarks.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-state-icon">📊</div>
          <h3>No benchmarks yet</h3>
          <p>Run your first benchmark to analyze driver latency.</p>
          <button className="btn btn-primary" onClick={handleRunBenchmark} style={{ marginTop: '1rem' }}>
            Run Benchmark
          </button>
        </div>
      ) : (
        <div className="card">
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {benchmarks.map(b => (
                  <tr key={b.id}>
                    <td>{b.id.slice(0, 8)}...</td>
                    <td>{b.name}</td>
                    <td><span className={`badge badge-${b.status === 'completed' ? 'success' : b.status === 'running' ? 'info' : 'warning'}`}>{b.status}</span></td>
                    <td>{new Date(b.created_at).toLocaleString()}</td>
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