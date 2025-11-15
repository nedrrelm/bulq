import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { authApi } from '../api/auth'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import type { User } from '../schemas/user'
import { getErrorMessage } from '../utils/errorHandling'

interface ChangeUsernamePopupProps {
  onClose: () => void
  onSuccess: (updatedUser: User) => void
}

export default function ChangeUsernamePopup({ onClose, onSuccess }: ChangeUsernamePopupProps) {
  const { t } = useTranslation(['common', 'profile'])
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
      setError(t('profile:validation.usernameMinLength'))
      return
    }

    if (!/^[a-zA-Z0-9_-]+$/.test(newUsername)) {
      setError(t('profile:validation.usernameInvalidChars'))
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
          <h2>{t('profile:changeUsername.title')}</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="new-username" className="form-label">{t('profile:fields.username')} *</label>
            <input
              id="new-username"
              type="text"
              className="form-input"
              value={newUsername}
              onChange={(e) => {
                setNewUsername(e.target.value)
                setError('')
              }}
              placeholder={t('profile:fields.username')}
              disabled={submitting}
              minLength={3}
              maxLength={50}
              required
              autoFocus
            />
            <small style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem', display: 'block' }}>
              {t('profile:changeUsername.hint')}
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="current-password" className="form-label">{t('profile:fields.currentPassword')} *</label>
            <input
              id="current-password"
              type="password"
              className="form-input"
              value={currentPassword}
              onChange={(e) => {
                setCurrentPassword(e.target.value)
                setError('')
              }}
              placeholder={t('profile:fields.currentPassword')}
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
              {t('common:buttons.cancel')}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? t('profile:changeUsername.changing') : t('common:buttons.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
