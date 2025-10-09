import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useNotifications } from '../contexts/NotificationContext'
import { NotificationItem } from './NotificationItem'

interface NotificationDropdownProps {
  onClose: () => void
}

export function NotificationDropdown({ onClose }: NotificationDropdownProps) {
  const navigate = useNavigate()
  const { notifications, fetchNotifications, markAllAsRead, markAsRead } = useNotifications()

  useEffect(() => {
    fetchNotifications()
  }, [])

  const handleMarkAllAsRead = async () => {
    await markAllAsRead()
  }

  const handleSeeMore = () => {
    onClose()
    navigate('/notifications')
  }

  const handleNotificationClick = async (notificationId: string) => {
    if (!notifications.find(n => n.id === notificationId)?.read) {
      await markAsRead(notificationId)
    }
    onClose()
  }

  // Show last 3 notifications (even if read)
  const recentNotifications = notifications.slice(0, 3)

  return (
    <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h3 className="text-lg font-semibold">Notifications</h3>
        {notifications.some(n => !n.read) && (
          <button
            onClick={handleMarkAllAsRead}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Mark all as read
          </button>
        )}
      </div>

      <div className="max-h-96 overflow-y-auto">
        {recentNotifications.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500">
            No notifications yet
          </div>
        ) : (
          <>
            {recentNotifications.map(notification => (
              <NotificationItem
                key={notification.id}
                notification={notification}
                onClick={() => handleNotificationClick(notification.id)}
              />
            ))}
          </>
        )}
      </div>

      {notifications.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-200">
          <button
            onClick={handleSeeMore}
            className="w-full text-center text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            See all notifications
          </button>
        </div>
      )}
    </div>
  )
}
