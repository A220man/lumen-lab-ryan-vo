// Hyprland page - placeholder
import { useState, useEffect } from 'react'
import { api } from '../api/client'

interface HyprlandConfig {
  enabled: boolean
  synthetic_seat: string
  operator_authorization: boolean
}

export function HyprlandPage() {
  const [config, setConfig] = useState<HyprlandConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      setLoading(true)
      const data = await api.get<HyprlandConfig>('/api/v1/hyprland/config')
      setConfig(data)
    } catch (err) {
      setError('Failed to load Hyprland configuration')
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
        <button className="btn btn-primary" onClick={fetchConfig}>Retry</button>
      </div>
    )
  }

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>Hyprland Isolated Input</h1>

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>Configuration</h2>
        {config ? (
          <dl style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.5rem 1.5rem' }}>
            <dt style={{ fontWeight: 500, color: '#6b7280' }}>Enabled</dt>
            <dd><span className={`badge badge-${config.enabled ? 'success' : 'warning'}`}>{config.enabled ? 'Yes' : 'No'}</span></dd>
            <dt style={{ fontWeight: 500, color: '#6b7280' }}>Synthetic Seat</dt>
            <dd>{config.synthetic_seat || 'Not configured'}</dd>
            <dt style={{ fontWeight: 500, color: '#6b7280' }}>Operator Authorization</dt>
            <dd><span className={`badge badge-${config.operator_authorization ? 'success' : 'error'}`}>{config.operator_authorization ? 'Configured' : 'Not configured'}</span></dd>
          </dl>
        ) : (
          <p style={{ color: '#6b7280' }}>Configuration not available</p>
        )}
      </div>

      <div className="card" style={{ marginTop: '1.5rem' }}>
        <h2 style={{ marginBottom: '1rem' }}>Actions</h2>
        <button className="btn btn-primary" disabled>
          Authorize Session
        </button>
      </div>
    </div>
  )
}