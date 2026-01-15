import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import { authApi } from '../api/auth'
import type { UserStats } from '../schemas/user'
import { Package, DollarSign, Users, ShoppingCart, HandHelping, Crown } from 'lucide-react'
import ChangeNamePopup from '../components/ChangeNamePopup'
import ChangeUsernamePopup from '../components/ChangeUsernamePopup'
import ChangePasswordPopup from '../components/ChangePasswordPopup'
import { logger } from '../utils/logger'
import '../styles/pages/ProfilePage.css'

export default function ProfilePage() {
  const { t } = useTranslation(['profile'])
  const { user, updateUser } = useAuth()
  const [stats, setStats] = useState<UserStats | null>(null)
  const [loadingStats, setLoadingStats] = useState(true)

  // Popup states
  const [showNamePopup, setShowNamePopup] = useState(false)
  const [showUsernamePopup, setShowUsernamePopup] = useState(false)
  const [showPasswordPopup, setShowPasswordPopup] = useState(false)

  // Success messages
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    setLoadingStats(true)
    try {
      const data = await authApi.getProfileStats()
      setStats(data)
    } catch (err) {
      logger.error('Failed to fetch profile stats:', err)
    } finally {
      setLoadingStats(false)
    }
  }

  const handleNameSuccess = (updatedUser: any) => {
    updateUser(updatedUser)
    setShowNamePopup(false)
    setSuccessMessage(t('profile:messages.nameChanged'))
    setTimeout(() => setSuccessMessage(''), 3000)
  }

  const handleUsernameSuccess = (updatedUser: any) => {
    updateUser(updatedUser)
    setShowUsernamePopup(false)
    setSuccessMessage(t('profile:messages.usernameChanged'))
    setTimeout(() => setSuccessMessage(''), 3000)
  }

  const handlePasswordSuccess = () => {
    setShowPasswordPopup(false)
    setSuccessMessage(t('profile:messages.passwordChanged'))
    setTimeout(() => setSuccessMessage(''), 3000)
  }

  const handleDarkModeToggle = async () => {
    try {
      const updatedUser = await authApi.toggleDarkMode()
      updateUser(updatedUser)
      // Apply dark mode class to body immediately
      if (updatedUser.dark_mode) {
        document.body.classList.add('dark-mode')
      } else {
        document.body.classList.remove('dark-mode')
      }
    } catch (err) {
      logger.error('Failed to toggle dark mode:', err)
    }
  }

  const handleLanguageChange = async (newLanguage: string) => {
    try {
      const updatedUser = await authApi.changeLanguage(newLanguage)
      updateUser(updatedUser)
      // i18n language will be synced automatically via AuthContext useEffect
    } catch (err) {
      logger.error('Failed to change language:', err)
    }
  }

  if (!user) return null

  return (
    <div className="profile-page">
      <h1>{t('profile:title')}</h1>

      {/* Success Message */}
      {successMessage && (
        <div className="alert alert-success" style={{ marginBottom: '2rem' }}>
          {successMessage}
        </div>
      )}

      {/* User Info */}
      <div className="profile-header">
        <div className="user-info-card">
          <div className="user-avatar">
            <Users size={48} />
          </div>
          <div>
            <h2>{user.name}</h2>
            <p className="username">@{user.username}</p>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="profile-section">
        <h2>{t('profile:sections.statistics')}</h2>
        {loadingStats ? (
          <p>{t('profile:messages.loadingStats')}</p>
        ) : stats ? (
          <div className="stats-grid">
            <div className="stat-card">
              <Package className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.total_quantity_bought.toFixed(2)}</div>
                <div className="stat-label">{t('profile:stats.totalQuantityBought')}</div>
              </div>
            </div>

            <div className="stat-card">
              <DollarSign className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.total_money_spent.toFixed(2)} RSD</div>
                <div className="stat-label">{t('profile:stats.totalMoneySpent')}</div>
              </div>
            </div>

            <div className="stat-card">
              <ShoppingCart className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.runs_participated}</div>
                <div className="stat-label">{t('profile:stats.runsParticipated')}</div>
              </div>
            </div>

            <div className="stat-card">
              <HandHelping className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.runs_helped}</div>
                <div className="stat-label">{t('profile:stats.runsHelped')}</div>
              </div>
            </div>

            <div className="stat-card">
              <Crown className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.runs_led}</div>
                <div className="stat-label">{t('profile:stats.runsLed')}</div>
              </div>
            </div>

            <div className="stat-card">
              <Users className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.groups_count}</div>
                <div className="stat-label">{t('profile:stats.groups')}</div>
              </div>
            </div>
          </div>
        ) : (
          <p>{t('profile:errors.failedToLoadStats')}</p>
        )}
      </div>

      {/* Account Settings */}
      <div className="profile-section">
        <h2>{t('profile:sections.accountSettings')}</h2>
        <div className="settings-actions">
          <div className="setting-item">
            <div>
              <h3>{t('profile:fields.language')}</h3>
              <p>{t('profile:descriptions.chooseLanguage')}</p>
            </div>
            <select
              className="language-select"
              value={user.preferred_language || 'en'}
              onChange={(e) => handleLanguageChange(e.target.value)}
            >
              <option value="en">English</option>
              <option value="ru">Русский (Russian)</option>
              <option value="sr">Српски (Serbian)</option>
            </select>
          </div>

          <div className="setting-item">
            <div>
              <h3>{t('profile:fields.darkMode')}</h3>
              <p>{t('profile:descriptions.toggleDarkMode')}</p>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={user.dark_mode || false}
                onChange={handleDarkModeToggle}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          <div className="setting-item">
            <div>
              <h3>{t('profile:fields.name')}</h3>
              <p>{t('profile:descriptions.changeName')}</p>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setShowNamePopup(true)}
            >
              {t('profile:actions.changeName')}
            </button>
          </div>

          <div className="setting-item">
            <div>
              <h3>{t('profile:fields.username')}</h3>
              <p>{t('profile:descriptions.changeUsername')}</p>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setShowUsernamePopup(true)}
            >
              {t('profile:actions.changeUsername')}
            </button>
          </div>

          <div className="setting-item">
            <div>
              <h3>{t('profile:fields.password')}</h3>
              <p>{t('profile:descriptions.changePassword')}</p>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setShowPasswordPopup(true)}
            >
              {t('profile:actions.changePassword')}
            </button>
          </div>
        </div>
      </div>

      {/* Popups */}
      {showNamePopup && (
        <ChangeNamePopup
          onClose={() => setShowNamePopup(false)}
          onSuccess={handleNameSuccess}
        />
      )}

      {showUsernamePopup && (
        <ChangeUsernamePopup
          onClose={() => setShowUsernamePopup(false)}
          onSuccess={handleUsernameSuccess}
        />
      )}

      {showPasswordPopup && (
        <ChangePasswordPopup
          onClose={() => setShowPasswordPopup(false)}
          onSuccess={handlePasswordSuccess}
        />
      )}
    </div>
  )
}
