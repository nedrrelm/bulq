import { useEffect, useState } from 'react'
import { useNotifications } from '../contexts/NotificationContext'
import { NotificationItem } from '../components/NotificationItem'
import LoadingSpinner from '../components/LoadingSpinner'

const LIMIT = 100

export default function NotificationPage() {
  const { notifications, fetchNotifications, markAsRead, markAllAsRead, loading } = useNotifications()
  const [offset, setOffset] = useState(0)

  useEffect(() => {
    fetchNotifications(LIMIT, offset)
  }, [offset, fetchNotifications])

  const handleNotificationClick = async (notificationId: string) => {
    if (!notifications.find(n => n.id === notificationId)?.read) {
      await markAsRead(notificationId)
    }
  }

  const handleMarkAllAsRead = async () => {
    await markAllAsRead()
  }

  const handlePrevPage = () => {
    setOffset(Math.max(0, offset - LIMIT))
  }

  const handleNextPage = () => {
    setOffset(offset + LIMIT)
  }

  const unreadCount = notifications.filter(n => !n.read).length
  const hasMorePages = notifications.length === LIMIT
  const showPagination = offset > 0 || hasMorePages

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
          <>
            <div className="notification-list">
              {notifications.map(notification => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onClick={() => handleNotificationClick(notification.id)}
                />
              ))}
            </div>

            {showPagination && (
              <div className="pagination-controls">
                <button
                  onClick={handlePrevPage}
                  disabled={offset === 0}
                  className="btn btn-secondary"
                >
                  Previous
                </button>
                <span className="pagination-info">
                  Showing {offset + 1}-{offset + notifications.length}
                </span>
                <button
                  onClick={handleNextPage}
                  disabled={!hasMorePages}
                  className="btn btn-secondary"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
