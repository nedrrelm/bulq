import { useNavigate } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import type { Notification } from '../types/notification'

interface NotificationItemProps {
  notification: Notification
  onClick?: () => void
}

export function NotificationItem({ notification, onClick }: NotificationItemProps) {
  const navigate = useNavigate()

  const getNotificationMessage = () => {
    if (notification.type === 'run_state_changed') {
      const { store_name, old_state, new_state, group_id } = notification.data

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

      const message = `Run at ${store_name} ${stateMessages[new_state] || `changed to ${new_state}`}`

      if (notification.grouped && notification.count) {
        return `${notification.count} state changes for ${store_name} run`
      }

      return message
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

  const handleClick = () => {
    if (onClick) {
      onClick()
    }

    // Navigate to the run page
    if (notification.type === 'run_state_changed' ||
        notification.type === 'leader_reassignment_request' ||
        notification.type === 'leader_reassignment_accepted' ||
        notification.type === 'leader_reassignment_declined') {
      const { run_id } = notification.data
      if (run_id) {
        navigate(`/runs/${run_id}`)
      }
    }
  }

  const timeAgo = (() => {
    try {
      if (!notification.created_at) return 'Just now'
      const date = new Date(notification.created_at)
      if (isNaN(date.getTime())) return 'Just now'
      return formatDistanceToNow(date, { addSuffix: true })
    } catch {
      return 'Just now'
    }
  })()

  return (
    <button
      onClick={handleClick}
      style={{
        width: '100%',
        textAlign: 'left',
        padding: '1rem',
        backgroundColor: !notification.read ? '#eff6ff' : 'white',
        border: 'none',
        borderBottom: '1px solid #f3f4f6',
        cursor: 'pointer',
        transition: 'background-color 0.15s'
      }}
      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = !notification.read ? '#dbeafe' : '#f9fafb'}
      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = !notification.read ? '#eff6ff' : 'white'}
    >
      <div style={{ display: 'flex', alignItems: 'start', justifyContent: 'space-between' }}>
        <div style={{ flex: 1 }}>
          <p style={{
            fontSize: '0.875rem',
            fontWeight: !notification.read ? '600' : '400',
            margin: 0,
            marginBottom: '0.25rem'
          }}>
            {getNotificationMessage()}
          </p>
          <p style={{ fontSize: '0.75rem', color: '#6b7280', margin: 0 }}>{timeAgo}</p>
        </div>
        {!notification.read && (
          <span style={{
            marginLeft: '0.5rem',
            width: '0.5rem',
            height: '0.5rem',
            backgroundColor: '#2563eb',
            borderRadius: '50%',
            flexShrink: 0,
            marginTop: '0.25rem'
          }}></span>
        )}
      </div>
    </button>
  )
}
