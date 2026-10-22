// Auth hook - placeholder for OIDC Keycloak integration
import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

interface User {
  sub: string
  preferred_username?: string
  email?: string
  roles?: string[]
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  login: () => void
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    const initAuth = async () => {
      // TODO: Implement session check with Keycloak
      setLoading(false)
    }
    initAuth()
  }, [])

  const login = () => {
    // TODO: Redirect to Keycloak login with PKCE
    window.location.href = '/api/v1/auth/login'
  }

  const logout = async () => {
    // TODO: Call logout endpoint and clear local state
    setUser(null)
    window.location.href = '/api/v1/auth/logout'
  }

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      loading,
      login,
      logout,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}