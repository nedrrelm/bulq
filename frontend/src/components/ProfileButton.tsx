import { User } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

export function ProfileButton() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  return (
    <button
      onClick={() => navigate('/profile')}
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
      aria-label={t('profile.title')}
    >
      <User size={24} />
    </button>
  )
}
