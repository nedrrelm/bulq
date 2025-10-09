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
      // Skip auth check if we just logged out (to avoid 401 error)
      const justLoggedOut = sessionStorage.getItem('just_logged_out')
      if (justLoggedOut) {
        sessionStorage.removeItem('just_logged_out')
        setLoading(false)
        return
      }

      // Always try to fetch current user - the browser will automatically
      // send the httpOnly cookie with the request
      try {
        const userData = await authApi.getCurrentUser()
        setUser(userData)
      } catch (err) {
        // User not logged in (or session expired), which is fine
        // The user will see the login page
      } finally {
        setLoading(false)
      }
    }

    // Add small delay to avoid duplicate requests from React strict mode
    const authCheckTimeout = setTimeout(() => {
      checkAuth()
    }, 100)

    return () => clearTimeout(authCheckTimeout)
  }, [])

  const login = (userData: User) => {
    setUser(userData)
  }

  const logout = async () => {
    try {
      await authApi.logout()
      setUser(null)
      // Set flag to skip auth check after redirect (prevents 401 error)
      sessionStorage.setItem('just_logged_out', 'true')
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
