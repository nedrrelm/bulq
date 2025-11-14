import { useState, useRef } from 'react'
import { authApi } from '../api/auth'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import type { User } from '../schemas/user'
import { getErrorMessage } from '../utils/errorHandling'

interface ChangeUsernamePopupProps {
  onClose: () => void
  onSuccess: (updatedUser: User) => void
}

export default function ChangeUsernamePopup({ onClose, onSuccess }: ChangeUsernamePopupProps) {
  const [newUsername, setNewUsername] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (newUsername.length < 3) {
      setError('Username must be at least 3 characters')
      return
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(newUsername)) {
      setError('Username can only contain letters, numbers, hyphens, and underscores')
      return
    }

    try {
      setSubmitting(true)
      const updatedUser = await authApi.changeUsername(currentPassword, newUsername)
      onSuccess(updatedUser)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to change username'))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Change Username</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="new-username" className="form-label">New Username *</label>
            <input
              id="new-username"
              type="text"
              className="form-input"
              value={newUsername}
              onChange={(e) => {
                setNewUsername(e.target.value)
                setError('')
              }}
              placeholder="Enter new username"
              disabled={submitting}
              minLength={3}
              maxLength={50}
              required
              autoFocus
            />
            <small style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem', display: 'block' }}>
              Letters, numbers, hyphens, and underscores only (3-50 characters)
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="current-password" className="form-label">Current Password (for confirmation) *</label>
            <input
              id="current-password"
              type="password"
              className="form-input"
              value={currentPassword}
              onChange={(e) => {
                setCurrentPassword(e.target.value)
                setError('')
              }}
              placeholder="Enter your current password"
              disabled={submitting}
              required
            />
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Changing...' : 'Change Username'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
