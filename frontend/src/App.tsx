// Main App component
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { BenchmarksPage } from './pages/BenchmarksPage'
import { SandboxesPage } from './pages/SandboxesPage'
import { HyprlandPage } from './pages/HyprlandPage'
import { LoginPage } from './pages/LoginPage'
import { useAuth } from './auth/useAuth'

export function App() {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div className="spinner" />
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={isAuthenticated ? <Layout /> : <Navigate to="/login" replace />}
      >
        <Route path="/" element={<HomePage />} />
        <Route path="/benchmarks" element={<BenchmarksPage />} />
        <Route path="/sandboxes" element={<SandboxesPage />} />
        <Route path="/hyprland" element={<HyprlandPage />} />
      </Route>
    </Routes>
  )
}