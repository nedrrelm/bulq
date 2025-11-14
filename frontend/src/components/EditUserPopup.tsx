import { useState, useRef } from 'react'
import { adminApi, type AdminUser } from '../api/admin'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { validateLength, sanitizeString } from '../utils/validation'
import { useConfirm } from '../hooks/useConfirm'
import ConfirmDialog from './ConfirmDialog'
import { getErrorMessage } from '../utils/errorHandling'
import { translateSuccess } from '../utils/translation'

interface EditUserPopupProps {
  user: AdminUser
  onClose: () => void
  onSuccess: () => void
}

const MAX_NAME_LENGTH = 100
const MIN_NAME_LENGTH = 2
const MAX_USERNAME_LENGTH = 50
const MIN_USERNAME_LENGTH = 3

export default function EditUserPopup({ user, onClose, onSuccess }: EditUserPopupProps) {
  const [userName, setUserName] = useState(user.name)
  const [username, setUsername] = useState(user.username)
  const [isAdmin, setIsAdmin] = useState(user.is_admin)
  const [verified, setVerified] = useState(user.verified)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

  useModalFocusTrap(modalRef, true, onClose)

  const validateUserName = (value: string): boolean => {
    const trimmed = value.trim()

    if (trimmed.length === 0) {
      setError('User name is required')
      return false
    }

    const lengthValidation = validateLength(trimmed, MIN_NAME_LENGTH, MAX_NAME_LENGTH, 'Name')
    if (!lengthValidation.isValid) {
      setError(lengthValidation.error || 'Invalid name')
      return false
    }

    return true
  }

  const validateUsername = (value: string): boolean => {
    const trimmed = value.trim()

    if (trimmed.length === 0) {
      setError('Username is required')
      return false
    }

    const lengthValidation = validateLength(trimmed, MIN_USERNAME_LENGTH, MAX_USERNAME_LENGTH, 'Username')
    if (!lengthValidation.isValid) {
      setError(lengthValidation.error || 'Invalid username')
      return false
    }

    // Check username format
    if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
      setError('Username can only contain letters, numbers, hyphens, and underscores')
      return false
    }

    return true
  }

  const handleNameChange = (value: string) => {
    const sanitized = sanitizeString(value, MAX_NAME_LENGTH)
    setUserName(sanitized)
    setError('')
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()

    setError('')

    if (!validateUserName(userName) || !validateUsername(username)) {
      return
    }

    try {
      setSubmitting(true)

      await adminApi.updateUser(user.id, {
        name: userName.trim(),
        username: username.trim().toLowerCase(),
        is_admin: isAdmin,
        verified: verified,
      })

      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to update user'))
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    try {
      setSubmitting(true)
      const response = await adminApi.deleteUser(user.id)
      alert(translateSuccess(response.code, response.details))
      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to delete user'))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal modal-scrollable" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Edit User</h2>
        </div>

        <form onSubmit={handleUpdate}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="user-name" className="form-label">Name *</label>
            <input
              id="user-name"
              type="text"
              className={`form-input ${error ? 'input-error' : ''}`}
              value={userName}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="Full name"
              disabled={submitting}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="username" className="form-label">Username *</label>
            <input
              id="username"
              type="text"
              className={`form-input ${error ? 'input-error' : ''}`}
              value={username}
              onChange={(e) => {
                setUsername(e.target.value)
                setError('')
              }}
              placeholder="username"
              disabled={submitting}
              minLength={MIN_USERNAME_LENGTH}
              maxLength={MAX_USERNAME_LENGTH}
              pattern="[a-zA-Z0-9_-]+"
              required
            />
            <small style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem' }}>
              Letters, numbers, hyphens, and underscores only (3-50 characters)
            </small>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={verified}
                onChange={(e) => {
                  setVerified(e.target.checked)
                  setError('')
                }}
                disabled={submitting}
              />
              <span>Verified</span>
            </label>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isAdmin}
                onChange={(e) => {
                  setIsAdmin(e.target.checked)
                  setError('')
                }}
                disabled={submitting}
              />
              <span>Admin</span>
            </label>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem', marginLeft: '1.5rem' }}>
              Note: You cannot remove your own admin status
            </p>
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
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>

        <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

        {/* Delete Section */}
        <div className="form-group">
          <label className="form-label" style={{ color: 'var(--color-danger)' }}>Danger Zone</label>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
            Delete this user permanently. This cannot be undone. You cannot delete yourself or other admin users.
          </p>
          <button
            type="button"
            className="btn"
            style={{ backgroundColor: 'var(--color-danger)', color: 'white' }}
            onClick={() => showConfirm(
              `Delete user "${user.name}"? This cannot be undone.`,
              handleDelete,
              { danger: true }
            )}
            disabled={submitting}
          >
            Delete User
          </button>
        </div>
      </div>

      {confirmState && (
        <ConfirmDialog
          message={confirmState.message}
          onConfirm={handleConfirm}
          onCancel={hideConfirm}
          danger={confirmState.danger}
        />
      )}
    </div>
  )
}
