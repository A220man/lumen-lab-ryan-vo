import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './auth/useAuth.tsx'
import { App } from './App'
import type { ReactNode } from 'react'

// Mock the auth hook to return authenticated state
vi.mock('./auth/useAuth.tsx', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./auth/useAuth.tsx')>()
  return {
    ...actual,
    useAuth: () => ({
      user: { sub: 'test-user', preferred_username: 'testuser', email: 'test@example.com', roles: ['viewer'] },
      isAuthenticated: true,
      loading: false,
      login: vi.fn(),
      logout: vi.fn(),
    }),
    AuthProvider: ({ children }: { children: ReactNode }) => <>{children}</>,
  }
})

describe('App', () => {
  it('renders navigation when authenticated', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    )

    // Check header navigation (links)
    expect(screen.getByRole('link', { name: 'Lumen Lab' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Dashboard' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Benchmarks' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Sandboxes' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Hyprland' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Logout' })).toBeInTheDocument()
  })

  it('renders logout button and user info', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    )

    expect(screen.getByText('testuser')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Logout' })).toBeInTheDocument()
  })
})