import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { authApi } from '../api/auth'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { getErrorMessage } from '../utils/errorHandling'

interface ChangePasswordPopupProps {
  onClose: () => void
  onSuccess: () => void
}

export default function ChangePasswordPopup({ onClose, onSuccess }: ChangePasswordPopupProps) {
  const { t } = useTranslation(['common', 'profile'])
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (newPassword.length < 6) {
      setError(t('profile:validation.passwordMinLength'))
      return
    }

    if (newPassword !== confirmPassword) {
      setError(t('profile:validation.passwordMismatch'))
      return
    }

    try {
      setSubmitting(true)
      await authApi.changePassword(currentPassword, newPassword)
      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to change password'))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('profile:changePassword.title')}</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

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
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="new-password" className="form-label">{t('profile:fields.newPassword')} *</label>
            <input
              id="new-password"
              type="password"
              className="form-input"
              value={newPassword}
              onChange={(e) => {
                setNewPassword(e.target.value)
                setError('')
              }}
              placeholder={t('profile:fields.newPassword')}
              disabled={submitting}
              minLength={6}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirm-password" className="form-label">{t('profile:fields.confirmPassword')} *</label>
            <input
              id="confirm-password"
              type="password"
              className="form-input"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value)
                setError('')
              }}
              placeholder={t('profile:fields.confirmPassword')}
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
              {submitting ? t('profile:changePassword.changing') : t('common:buttons.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
