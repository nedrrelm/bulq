import { useNavigate } from 'react-router-dom'
import { useNotifications } from '../contexts/NotificationContext'
import { NotificationItem } from './NotificationItem'

interface NotificationDropdownProps {
  onClose: () => void
}

export function NotificationDropdown({ onClose }: NotificationDropdownProps) {
  const navigate = useNavigate()
  const { notifications, markAllAsRead, markAsRead } = useNotifications()

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
    <div
      className="notification-dropdown"
      style={{
        position: 'absolute',
        right: 0,
        top: '100%',
        marginTop: '0.5rem',
        width: '24rem',
        maxWidth: '90vw',
        backgroundColor: 'white',
        borderRadius: '0.5rem',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        border: '1px solid #e5e7eb',
        zIndex: 9999
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.75rem 1rem',
          borderBottom: '1px solid #e5e7eb'
        }}
      >
        <h3 style={{ fontSize: '1.125rem', fontWeight: '600', margin: 0 }}>Notifications</h3>
        {notifications.some(n => !n.read) && (
          <button
            onClick={handleMarkAllAsRead}
            style={{
              fontSize: '0.875rem',
              color: '#2563eb',
              fontWeight: '500',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '0.25rem 0.5rem'
            }}
          >
            Mark all as read
          </button>
        )}
      </div>

      <div style={{ maxHeight: '24rem', overflowY: 'auto' }}>
        {recentNotifications.length === 0 ? (
          <div style={{ padding: '2rem 1rem', textAlign: 'center', color: '#6b7280' }}>
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

      <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid #e5e7eb' }}>
        <button
          onClick={handleSeeMore}
          style={{
            width: '100%',
            textAlign: 'center',
            fontSize: '0.875rem',
            color: '#2563eb',
            fontWeight: '500',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '0.5rem'
          }}
        >
          See all notifications
        </button>
      </div>
    </div>
  )
}
