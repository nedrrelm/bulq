import { useEffect } from 'react'
import { useNotifications } from '../contexts/NotificationContext'
import { NotificationItem } from '../components/NotificationItem'
import LoadingSpinner from '../components/LoadingSpinner'

export default function NotificationPage() {
  const { notifications, fetchNotifications, markAsRead, markAllAsRead, loading } = useNotifications()

  useEffect(() => {
    fetchNotifications()
  }, [])

  const handleNotificationClick = async (notificationId: string) => {
    if (!notifications.find(n => n.id === notificationId)?.read) {
      await markAsRead(notificationId)
    }
  }

  const handleMarkAllAsRead = async () => {
    await markAllAsRead()
  }

  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <div className="page-container">
      <div className="card card-lg">
        <div className="card-header">
          <h2>Notifications</h2>
          {unreadCount > 0 && (
            <button
              onClick={handleMarkAllAsRead}
              className="btn btn-ghost"
            >
              Mark all as read
            </button>
          )}
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : notifications.length === 0 ? (
          <div className="empty-state">
            <p>No notifications yet</p>
          </div>
        ) : (
          <div className="notification-list">
            {notifications.map(notification => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onClick={() => handleNotificationClick(notification.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
