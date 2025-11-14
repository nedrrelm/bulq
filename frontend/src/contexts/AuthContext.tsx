import { createContext, useContext, useEffect, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useCurrentUser, useLogout, authKeys } from '../hooks/queries'
import type { User } from '../types/user'
import { logger } from '../utils/logger'
import i18n from '../i18n/config'

interface AuthContextType {
  user: User | null | undefined
  login: (userData: User) => void
  logout: () => Promise<void>
  updateUser: (userData: User) => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  // Use React Query to manage current user state
  const { data: user, isLoading: loading, isError } = useCurrentUser()
  const logoutMutation = useLogout()

  const login = (userData: User) => {
    // Set current user data in React Query cache
    queryClient.setQueryData(authKeys.currentUser(), userData)
  }

  const updateUser = (userData: User) => {
    // Update current user data in React Query cache
    queryClient.setQueryData(authKeys.currentUser(), userData)
  }

  const logout = async () => {
    try {
      // Set flag before logout to prevent immediate re-fetch
      sessionStorage.setItem('just_logged_out', 'true')
      await logoutMutation.mutateAsync()
      // Force a hard reload to clear all state
      window.location.href = '/'
    } catch (err) {
      logger.error('Logout failed:', err)
      sessionStorage.removeItem('just_logged_out')
    }
  }

  // Sync i18n language when user loads or changes
  useEffect(() => {
    if (user?.preferred_language) {
      i18n.changeLanguage(user.preferred_language)
    }
  }, [user?.preferred_language])

  return (
    <AuthContext.Provider value={{
      user: isError ? null : user,
      login,
      logout,
      updateUser,
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
