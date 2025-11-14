import { useState, useEffect } from 'react'
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
    setSuccessMessage('Name changed successfully')
    setTimeout(() => setSuccessMessage(''), 3000)
  }

  const handleUsernameSuccess = (updatedUser: any) => {
    updateUser(updatedUser)
    setShowUsernamePopup(false)
    setSuccessMessage('Username changed successfully')
    setTimeout(() => setSuccessMessage(''), 3000)
  }

  const handlePasswordSuccess = () => {
    setShowPasswordPopup(false)
    setSuccessMessage('Password changed successfully')
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

  if (!user) return null

  return (
    <div className="profile-page">
      <h1>Profile</h1>

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
        <h2>Statistics</h2>
        {loadingStats ? (
          <p>Loading statistics...</p>
        ) : stats ? (
          <div className="stats-grid">
            <div className="stat-card">
              <Package className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.total_quantity_bought.toFixed(2)}</div>
                <div className="stat-label">Total Quantity Bought</div>
              </div>
            </div>

            <div className="stat-card">
              <DollarSign className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">${stats.total_money_spent.toFixed(2)}</div>
                <div className="stat-label">Total Money Spent</div>
              </div>
            </div>

            <div className="stat-card">
              <ShoppingCart className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.runs_participated}</div>
                <div className="stat-label">Runs Participated</div>
              </div>
            </div>

            <div className="stat-card">
              <HandHelping className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.runs_helped}</div>
                <div className="stat-label">Runs Helped</div>
              </div>
            </div>

            <div className="stat-card">
              <Crown className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.runs_led}</div>
                <div className="stat-label">Runs Led</div>
              </div>
            </div>

            <div className="stat-card">
              <Users className="stat-icon" size={32} />
              <div className="stat-content">
                <div className="stat-value">{stats.groups_count}</div>
                <div className="stat-label">Groups</div>
              </div>
            </div>
          </div>
        ) : (
          <p>Failed to load statistics</p>
        )}
      </div>

      {/* Account Settings */}
      <div className="profile-section">
        <h2>Account Settings</h2>
        <div className="settings-actions">
          <div className="setting-item">
            <div>
              <h3>Dark Mode</h3>
              <p>Toggle dark mode theme</p>
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
              <h3>Name</h3>
              <p>Change your display name</p>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setShowNamePopup(true)}
            >
              Change Name
            </button>
          </div>

          <div className="setting-item">
            <div>
              <h3>Username</h3>
              <p>Change your login username</p>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setShowUsernamePopup(true)}
            >
              Change Username
            </button>
          </div>

          <div className="setting-item">
            <div>
              <h3>Password</h3>
              <p>Update your password</p>
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setShowPasswordPopup(true)}
            >
              Change Password
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
