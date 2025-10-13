import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authApi } from '../../api'
import type { User } from '../../types/user'

// Query Keys
export const authKeys = {
  all: ['auth'] as const,
  currentUser: () => [...authKeys.all, 'current-user'] as const,
}

// ==================== Queries ====================

/**
 * Get current authenticated user
 */
export function useCurrentUser() {
  return useQuery({
    queryKey: authKeys.currentUser(),
    queryFn: async () => {
      // Check if we just logged out to avoid unnecessary 401 errors
      const justLoggedOut = sessionStorage.getItem('just_logged_out')
      if (justLoggedOut) {
        sessionStorage.removeItem('just_logged_out')
        return null
      }

      try {
        return await authApi.getCurrentUser()
      } catch (error) {
        // Return null for auth errors to show login page
        return null
      }
    },
    staleTime: Infinity, // User data rarely changes, keep fresh until manually invalidated
    retry: false, // Don't retry if not authenticated
  })
}

// ==================== Mutations ====================

/**
 * Login mutation
 */
export function useLogin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (credentials: { email: string; password: string }) =>
      authApi.login(credentials.email, credentials.password),
    onSuccess: (userData) => {
      // Set the current user data
      queryClient.setQueryData(authKeys.currentUser(), userData)
    },
  })
}

/**
 * Logout mutation
 */
export function useLogout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => authApi.logout(),
    onSuccess: () => {
      // Clear all cached data on logout
      queryClient.clear()
    },
  })
}

/**
 * Register new user
 */
export function useRegister() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { name: string; email: string; password: string }) =>
      authApi.register(data.name, data.email, data.password),
    onSuccess: (userData) => {
      // Set the current user data after registration
      queryClient.setQueryData(authKeys.currentUser(), userData)
    },
  })
}
