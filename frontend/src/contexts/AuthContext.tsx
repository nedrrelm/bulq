import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '../api'
import type { User } from '../types/user'

interface AuthContextType {
  user: User | null
  login: (userData: User) => void
  logout: () => Promise<void>
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Check if user is already logged in
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await authApi.getCurrentUser()
        setUser(userData)
      } catch (err) {
        // User not logged in, which is fine
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = (userData: User) => {
    setUser(userData)
  }

  const logout = async () => {
    try {
      await authApi.logout()
      setUser(null)
      window.location.href = '/'
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
