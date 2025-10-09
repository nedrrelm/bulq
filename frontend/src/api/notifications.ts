import { api } from './client'
import type { Notification } from '../types/notification'

export interface GetNotificationsParams {
  limit?: number
  offset?: number
}

export const notificationsApi = {
  getNotifications: (params?: GetNotificationsParams) =>
    api.get<Notification[]>('/notifications', { params }),

  getUnreadNotifications: () =>
    api.get<Notification[]>('/notifications/unread'),

  getUnreadCount: () =>
    api.get<{ count: number }>('/notifications/count'),

  markAsRead: (notificationId: string) =>
    api.post<{ message: string }>(`/notifications/${notificationId}/mark-read`),

  markAllAsRead: () =>
    api.post<{ message: string; count: number }>('/notifications/mark-all-read')
}
