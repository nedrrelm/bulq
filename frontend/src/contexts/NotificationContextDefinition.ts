import { createContext } from 'react'
import type { Notification } from '../types/notification'

export interface NotificationContextType {
  notifications: Notification[]
  unreadCount: number
  fetchNotifications: (limit?: number, offset?: number) => Promise<void>
  markAsRead: (id: string) => Promise<void>
  markAllAsRead: () => Promise<void>
  refreshUnreadCount: () => Promise<void>
}

export const NotificationContext = createContext<NotificationContextType | undefined>(undefined)
