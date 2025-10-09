import { useState, useRef } from 'react'
import { Bell } from 'lucide-react'
import { useNotifications } from '../contexts/NotificationContext'
import { NotificationDropdown } from './NotificationDropdown'
import { useClickOutside } from '../hooks/useClickOutside'

export function NotificationBadge() {
  const { unreadCount, fetchNotifications } = useNotifications()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useClickOutside(dropdownRef, () => setIsOpen(false))

  const handleToggle = async () => {
    if (!isOpen) {
      // Fetch notifications when opening
      await fetchNotifications(20)
    }
    setIsOpen(!isOpen)
  }

  return (
    <div ref={dropdownRef} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={handleToggle}
        style={{
          position: 'relative',
          padding: '0.5rem',
          color: '#4b5563',
          background: 'none',
          border: 'none',
          borderRadius: '9999px',
          cursor: 'pointer',
          transition: 'all 0.15s'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = '#111827'
          e.currentTarget.style.backgroundColor = '#f3f4f6'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = '#4b5563'
          e.currentTarget.style.backgroundColor = 'transparent'
        }}
        aria-label="Notifications"
      >
        <Bell size={24} />
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute',
            top: 0,
            right: 0,
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0.125rem 0.5rem',
            fontSize: '0.75rem',
            fontWeight: 'bold',
            lineHeight: '1',
            color: 'white',
            backgroundColor: '#dc2626',
            borderRadius: '9999px',
            transform: 'translate(50%, -50%)'
          }}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && <NotificationDropdown onClose={() => setIsOpen(false)} />}
    </div>
  )
}
