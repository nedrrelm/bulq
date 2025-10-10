import { createContext, useContext, ReactNode, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useCurrentUser, useLogout as useLogoutMutation, authKeys } from '../hooks/queries'
import type { User } from '../types/user'

interface AuthContextType {
  user: User | null | undefined
  login: (userData: User) => void
  logout: () => Promise<void>
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  // Use React Query to manage current user state
  const { data: user, isLoading: loading, isError } = useCurrentUser()
  const logoutMutation = useLogoutMutation()

  // Handle logout flag from sessionStorage
  useEffect(() => {
    const justLoggedOut = sessionStorage.getItem('just_logged_out')
    if (justLoggedOut) {
      sessionStorage.removeItem('just_logged_out')
      // Clear React Query cache if just logged out
      queryClient.clear()
    }
  }, [queryClient])

  const login = (userData: User) => {
    // Set current user data in React Query cache
    queryClient.setQueryData(authKeys.currentUser(), userData)
  }

  const logout = async () => {
    try {
      await logoutMutation.mutateAsync()
      // Set flag to skip auth check after redirect (prevents 401 error)
      sessionStorage.setItem('just_logged_out', 'true')
      window.location.href = '/'
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  return (
    <AuthContext.Provider value={{
      user: isError ? null : user,
      login,
      logout,
      loading
    }}>
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
