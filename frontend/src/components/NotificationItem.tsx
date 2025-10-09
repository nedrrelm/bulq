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

    return 'New notification'
  }

  const handleClick = () => {
    if (onClick) {
      onClick()
    }

    // Navigate to the run page
    if (notification.type === 'run_state_changed') {
      const { run_id, group_id } = notification.data
      navigate(`/groups/${group_id}/runs/${run_id}`)
    }
  }

  const timeAgo = formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })

  return (
    <button
      onClick={handleClick}
      className={`w-full text-left p-4 hover:bg-gray-50 transition-colors border-b border-gray-100 ${
        !notification.read ? 'bg-blue-50' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className={`text-sm ${!notification.read ? 'font-semibold' : ''}`}>
            {getNotificationMessage()}
          </p>
          <p className="text-xs text-gray-500 mt-1">{timeAgo}</p>
        </div>
        {!notification.read && (
          <span className="ml-2 w-2 h-2 bg-blue-600 rounded-full flex-shrink-0 mt-1"></span>
        )}
      </div>
    </button>
  )
}
