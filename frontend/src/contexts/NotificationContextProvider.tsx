import { useState, useEffect, type ReactNode, useCallback } from 'react'
import { notificationsApi } from '../api'
import type { Notification } from '../types/notification'
import type { WebSocketMessage } from '../types/websocket'
import { useAuth } from '../hooks/useAuth'
import { useWebSocket } from '../hooks/useWebSocket'
import Toast from '../components/common/Toast'
import { WS_BASE_URL } from '../config'
import { logger } from '../utils/logger'
import { NotificationContext } from './NotificationContextDefinition'

export function NotificationProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  // Get the toast message for the notification type
  const getNotificationMessage = (notification: Notification): string => {
    const { type, data } = notification

    // Format notification messages based on type
    switch (type) {
      case 'run_state_changed':
        return `Run "${data.run_name}" is now ${data.new_state}`
      case 'bid_placed':
        return `${data.user_name} placed a bid in "${data.run_name}"`
      case 'bid_retracted':
        return `${data.user_name} retracted their bid in "${data.run_name}"`
      case 'user_joined_run':
        return `${data.user_name} joined "${data.run_name}"`
      case 'user_left_run':
        return `${data.user_name} left "${data.run_name}"`
      case 'leader_assigned':
        return `You are now the leader of "${data.run_name}"`
      case 'helper_assigned':
        return `You are now helping with "${data.run_name}"`
      case 'member_joined_group':
        return `${data.user_name} joined "${data.group_name}"`
      case 'member_left_group':
        return `${data.user_name} left "${data.group_name}"`
      case 'member_removed':
        return `${data.removed_user_name} was removed from "${data.group_name}"`
      case 'leader_reassignment_requested':
        return `Leadership transfer requested for "${data.run_name}"`
      case 'leader_reassignment_accepted':
        return `${data.new_leader_name} is now leading "${data.run_name}"`
      case 'leader_reassignment_rejected':
        return `Leadership transfer rejected for "${data.run_name}"`
      default:
        return 'New notification'
    }
  }

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'new_notification') {
      const newNotification: Notification = message.data

      // Add to notifications list
      setNotifications(prev => [newNotification, ...prev])

      // Increment unread count
      setUnreadCount(prev => prev + 1)

      // Show toast notification
      const message_text = getNotificationMessage(newNotification)
      setToastMessage(message_text)
    }
  }, [])

  // Connect to WebSocket for real-time notifications
  useWebSocket(
    user ? `${WS_BASE_URL}/ws/user` : null,
    {
      onMessage: handleWebSocketMessage,
      reconnectInterval: 3000,
      maxReconnectAttempts: 5
    }
  )

  // Fetch notifications
  const fetchNotifications = useCallback(async (limit: number = 10, offset: number = 0) => {
    if (!user) return

    try {
      const data = await notificationsApi.getNotifications(limit, offset)
      if (offset === 0) {
        setNotifications(data)
      } else {
        setNotifications(prev => [...prev, ...data])
      }
    } catch (error) {
      logger.error('Failed to fetch notifications:', error)
    }
  }, [user])

  // Fetch unread count
  const refreshUnreadCount = useCallback(async () => {
    if (!user) return

    try {
      const count = await notificationsApi.getUnreadCount()
      setUnreadCount(count)
    } catch (error) {
      logger.error('Failed to fetch unread count:', error)
    }
  }, [user])

  // Mark notification as read
  const markAsRead = useCallback(async (id: string) => {
    try {
      await notificationsApi.markAsRead(id)

      // Update local state
      setNotifications(prev =>
        prev.map(n => n.id === id ? { ...n, read: true } : n)
      )
      setUnreadCount(prev => Math.max(0, prev - 1))
    } catch (error) {
      logger.error('Failed to mark notification as read:', error)
    }
  }, [])

  // Mark all notifications as read
  const markAllAsRead = useCallback(async () => {
    try {
      await notificationsApi.markAllAsRead()

      // Update local state
      setNotifications(prev => prev.map(n => ({ ...n, read: true })))
      setUnreadCount(0)
    } catch (error) {
      logger.error('Failed to mark all notifications as read:', error)
    }
  }, [])

  // Initial load when user logs in
  useEffect(() => {
    if (user) {
      fetchNotifications()
      refreshUnreadCount()
    } else {
      // Clear notifications when user logs out
      setNotifications([])
      setUnreadCount(0)
    }
  }, [user, fetchNotifications, refreshUnreadCount])

  return (
    <NotificationContext.Provider value={{
      notifications,
      unreadCount,
      fetchNotifications,
      markAsRead,
      markAllAsRead,
      refreshUnreadCount
    }}>
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
