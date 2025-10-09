import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { notificationsApi } from '../api'
import type { Notification } from '../types/notification'
import { useAuth } from './AuthContext'
import { useWebSocket } from '../hooks/useWebSocket'
import Toast from '../components/Toast'

interface NotificationContextType {
  notifications: Notification[]
  unreadCount: number
  loading: boolean
  fetchNotifications: (limit?: number) => Promise<void>
  markAsRead: (notificationId: string) => Promise<void>
  markAllAsRead: () => Promise<void>
  refreshUnreadCount: () => Promise<void>
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined)

export function NotificationProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  // Construct WebSocket URL
  const wsUrl = user ? (() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.hostname
    const port = import.meta.env.DEV ? '8000' : window.location.port
    return `${protocol}//${host}:${port}/ws/user`
  })() : null

  const getNotificationMessage = (notification: Notification): string => {
    if (notification.type === 'run_state_changed') {
      const { store_name, new_state } = notification.data
      const stateMessages: Record<string, string> = {
        planning: 'is being planned',
        active: 'is now active',
        confirmed: 'has been confirmed',
        shopping: 'shopping has started',
        adjusting: 'needs bid adjustments',
        distributing: 'is ready for distribution',
        completed: 'has been completed',
        cancelled: 'has been cancelled'
      }
      return `Run at ${store_name} ${stateMessages[new_state] || `changed to ${new_state}`}`
    }

    if (notification.type === 'leader_reassignment_request') {
      const { from_user_name, store_name } = notification.data
      return `${from_user_name} wants to transfer leadership of ${store_name} run to you`
    }

    if (notification.type === 'leader_reassignment_accepted') {
      const { new_leader_name, store_name } = notification.data
      return `${new_leader_name} accepted leadership of ${store_name} run`
    }

    if (notification.type === 'leader_reassignment_declined') {
      const { declined_by_name, store_name } = notification.data
      return `${declined_by_name} declined leadership of ${store_name} run`
    }

    return 'New notification'
  }

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'new_notification') {
      const newNotification: Notification = message.data

      // Add to notifications list
      setNotifications(prev => [newNotification, ...prev])

      // Increment unread count
      setUnreadCount(prev => prev + 1)

      // Show toast notification
      setToastMessage(getNotificationMessage(newNotification))
    }
  }, [])

  // Connect to WebSocket for real-time notifications
  useWebSocket(wsUrl, {
    onMessage: handleWebSocketMessage
  })

  // Fetch unread count when user logs in
  useEffect(() => {
    if (user) {
      refreshUnreadCount()
    } else {
      setNotifications([])
      setUnreadCount(0)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  const fetchNotifications = useCallback(async (limit: number = 20) => {
    if (!user) return

    setLoading(true)
    try {
      const data = await notificationsApi.getNotifications({ limit })
      setNotifications(data)
    } catch (err) {
      console.error('Failed to fetch notifications:', err)
    } finally {
      setLoading(false)
    }
  }, [user])

  const refreshUnreadCount = useCallback(async () => {
    if (!user) return

    try {
      const data = await notificationsApi.getUnreadCount()
      setUnreadCount(data.count)
    } catch (err) {
      console.error('Failed to fetch unread count:', err)
    }
  }, [user])

  const markAsRead = async (notificationId: string) => {
    try {
      await notificationsApi.markAsRead(notificationId)

      // Update local state
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      )

      // Decrement unread count locally
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (err) {
      console.error('Failed to mark notification as read:', err)
    }
  }

  const markAllAsRead = async () => {
    try {
      await notificationsApi.markAllAsRead()

      // Update local state
      setNotifications(prev =>
        prev.map(n => ({ ...n, read: true }))
      )

      setUnreadCount(0)
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err)
    }
  }

  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        loading,
        fetchNotifications,
        markAsRead,
        markAllAsRead,
        refreshUnreadCount
      }}
    >
      {children}
      {toastMessage && (
        <Toast
          message={toastMessage}
          type="info"
          onClose={() => setToastMessage(null)}
          duration={5000}
        />
      )}
    </NotificationContext.Provider>
  )
}

export function useNotifications() {
  const context = useContext(NotificationContext)
  if (context === undefined) {
    throw new Error('useNotifications must be used within a NotificationProvider')
  }
  return context
}
