import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { useNotifications } from '../contexts/NotificationContext'
import { NotificationItem } from '../components/NotificationItem'

export function NotificationPage() {
  const navigate = useNavigate()
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

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center">
              <button
                onClick={() => navigate(-1)}
                className="mr-4 p-2 hover:bg-gray-100 rounded-full transition-colors"
                aria-label="Go back"
              >
                <ArrowLeft size={20} />
              </button>
              <h1 className="text-2xl font-bold">Notifications</h1>
            </div>
            {notifications.some(n => !n.read) && (
              <button
                onClick={handleMarkAllAsRead}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Mark all as read
              </button>
            )}
          </div>

          <div className="divide-y divide-gray-100">
            {loading ? (
              <div className="px-6 py-12 text-center text-gray-500">
                Loading notifications...
              </div>
            ) : notifications.length === 0 ? (
              <div className="px-6 py-12 text-center text-gray-500">
                No notifications yet
              </div>
            ) : (
              notifications.map(notification => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onClick={() => handleNotificationClick(notification.id)}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
