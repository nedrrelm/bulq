import { api } from './client'
import { notificationSchema, type Notification } from '../schemas/notification'
import { z } from 'zod'

export interface GetNotificationsParams {
  limit?: number
  offset?: number
}

const unreadCountResponseSchema = z.object({
  count: z.number()
})

const markAsReadResponseSchema = z.object({
  message: z.string()
})

const markAllAsReadResponseSchema = z.object({
  message: z.string(),
  count: z.number()
})

export const notificationsApi = {
  getNotifications: (_params?: GetNotificationsParams) =>
    api.get<Notification[]>('/notifications', z.array(notificationSchema)),

  getUnreadNotifications: () =>
    api.get<Notification[]>('/notifications/unread', z.array(notificationSchema)),

  getUnreadCount: () =>
    api.get<{ count: number }>('/notifications/count', unreadCountResponseSchema),

  markAsRead: (notificationId: string) =>
    api.post<{ message: string }>(`/notifications/${notificationId}/mark-read`, undefined, markAsReadResponseSchema),

  markAllAsRead: () =>
    api.post<{ message: string; count: number }>('/notifications/mark-all-read', undefined, markAllAsReadResponseSchema)
}
