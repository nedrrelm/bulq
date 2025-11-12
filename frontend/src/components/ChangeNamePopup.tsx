import { useState, useRef } from 'react'
import { authApi } from '../api/auth'
import { ApiError } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import type { User } from '../schemas/user'

interface ChangeNamePopupProps {
  onClose: () => void
  onSuccess: (updatedUser: User) => void
}

export default function ChangeNamePopup({ onClose, onSuccess }: ChangeNamePopupProps) {
  const [newName, setNewName] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (newName.trim().length < 1) {
      setError('Name cannot be empty')
      return
    }

    try {
      setSubmitting(true)
      const updatedUser = await authApi.changeName(currentPassword, newName.trim())
      onSuccess(updatedUser)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to change name')
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Change Name</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="new-name" className="form-label">New Name *</label>
            <input
              id="new-name"
              type="text"
              className="form-input"
              value={newName}
              onChange={(e) => {
                setNewName(e.target.value)
                setError('')
              }}
              placeholder="Enter new name"
              disabled={submitting}
              required
              autoFocus
            />
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
              {submitting ? 'Changing...' : 'Change Name'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
