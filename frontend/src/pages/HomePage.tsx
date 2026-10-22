// Home page dashboard
import { Link } from 'react-router-dom'

export function HomePage() {
  const cards = [
    {
      title: 'Benchmarks',
      description: 'Run and analyze driver latency benchmarks with configurable observation/settle delays',
      path: '/benchmarks',
      icon: '⚡',
    },
    {
      title: 'Sandboxes',
      description: 'Manage cross-OS sandbox environments with ARM64 support and GHCR publishing',
      path: '/sandboxes',
      icon: '📦',
    },
    {
      title: 'Hyprland',
      description: 'Configure isolated background input with synthetic seat authorization',
      path: '/hyprland',
      icon: '🖥️',
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: '0.5rem' }}>Lumen Lab</h1>
      <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
        Scale computer-use 2.0 with open-source drivers, cross-OS sandboxes, and benchmarks
        for training, evaluation, and data generation.
      </p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {cards.map(card => (
          <Link key={card.path} to={card.path} style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="card" style={{
              transition: 'transform 0.15s, box-shadow 0.15s',
              display: 'flex',
              flexDirection: 'column',
              height: '100%',
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{card.icon}</div>
              <h2 style={{ margin: '0 0 0.5rem', fontSize: '1.25rem' }}>{card.title}</h2>
              <p style={{ color: '#6b7280', fontSize: '0.875rem', flex: 1 }}>{card.description}</p>
              <span style={{ alignSelf: 'flex-start', marginTop: '1rem', color: '#2563eb', fontWeight: 500, fontSize: '0.875rem' }}>
                Open →
              </span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}