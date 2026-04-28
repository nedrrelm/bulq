import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { formatDistanceToNow } from 'date-fns'
import type { Notification } from '../types/notification'

interface NotificationItemProps {
  notification: Notification
  onClick?: () => void
}

export function NotificationItem({ notification, onClick }: NotificationItemProps) {
  const navigate = useNavigate()
  const { t } = useTranslation(['common', 'notifications'])

  const getNotificationMessage = () => {
    if (notification.type === 'run_state_changed') {
      const { store_name, new_state } = notification.data

      const stateMessages: Record<string, string> = {
        planning: t('notifications:states.planning'),
        active: t('notifications:states.active'),
        confirmed: t('notifications:states.confirmed'),
        shopping: t('notifications:states.shopping'),
        adjusting: t('notifications:states.adjusting'),
        distributing: t('notifications:states.distributing'),
        completed: t('notifications:states.completed'),
        cancelled: t('notifications:states.cancelled')
      }

      const message = t('notifications:runStateChanged', {
        store_name,
        state_message: new_state ? (stateMessages[new_state] || t('notifications:changedToState', { state: new_state })) : t('notifications:changedState')
      })

      if (notification.grouped && notification.count) {
        return t('notifications:groupedStateChanges', { count: notification.count, store_name })
      }

      return message
    }

    if (notification.type === 'leader_reassignment_request') {
      const { from_user_name, store_name } = notification.data
      return t('notifications:leadershipRequest', { from_user_name, store_name })
    }

    if (notification.type === 'leader_reassignment_accepted') {
      const { new_leader_name, store_name } = notification.data
      return t('notifications:leadershipAccepted', { new_leader_name, store_name })
    }

    if (notification.type === 'leader_reassignment_declined') {
      const { declined_by_name, store_name } = notification.data
      return t('notifications:leadershipDeclined', { declined_by_name, store_name })
    }

    return t('notifications:newNotification')
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
      if (!notification.created_at) return t('common:justNow')
      const date = new Date(notification.created_at)
      if (isNaN(date.getTime())) return t('common:justNow')
      return formatDistanceToNow(date, { addSuffix: true })
    } catch {
      return t('common:justNow')
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
