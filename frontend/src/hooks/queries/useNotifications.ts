import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '../../api'
import { createQueryKeys } from '../../utils/queryKeys'

// Query Keys
export const notificationKeys = createQueryKeys('notifications', {
  custom: {
    unread: (base: readonly string[]) => [...base, 'unread'] as const,
    count: (base: readonly string[]) => [...base, 'count'] as const
  }
})

// ==================== Queries ====================

/**
 * Get notifications for current user
 */
export function useNotifications(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: notificationKeys.list(params),
    queryFn: () => notificationsApi.getNotifications(params),
    staleTime: 10000, // Refetch after 10 seconds
  })
}

/**
 * Get unread notifications count
 */
export function useUnreadCount() {
  return useQuery({
    queryKey: notificationKeys.count(),
    queryFn: () => notificationsApi.getUnreadCount(),
    staleTime: 5000, // Refetch every 5 seconds
    refetchInterval: 30000, // Auto-refetch every 30 seconds
  })
}

// ==================== Mutations ====================

/**
 * Mark a notification as read
 */
export function useMarkNotificationRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (notificationId: string) => notificationsApi.markAsRead(notificationId),
    onSuccess: () => {
      // Invalidate notifications list and count
      queryClient.invalidateQueries({ queryKey: notificationKeys.all })
    },
  })
}

/**
 * Mark all notifications as read
 */
export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      // Invalidate notifications list and count
      queryClient.invalidateQueries({ queryKey: notificationKeys.all })
    },
  })
}
