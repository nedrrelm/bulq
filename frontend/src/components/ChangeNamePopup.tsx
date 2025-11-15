import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { authApi } from '../api/auth'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import type { User } from '../schemas/user'
import { getErrorMessage } from '../utils/errorHandling'

interface ChangeNamePopupProps {
  onClose: () => void
  onSuccess: (updatedUser: User) => void
}

export default function ChangeNamePopup({ onClose, onSuccess }: ChangeNamePopupProps) {
  const { t } = useTranslation(['common', 'profile'])
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
      setError(t('profile:validation.nameRequired'))
      return
    }

    try {
      setSubmitting(true)
      const updatedUser = await authApi.changeName(currentPassword, newName.trim())
      onSuccess(updatedUser)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to change name'))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('profile:changeName.title')}</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="new-name" className="form-label">{t('profile:fields.name')} *</label>
            <input
              id="new-name"
              type="text"
              className="form-input"
              value={newName}
              onChange={(e) => {
                setNewName(e.target.value)
                setError('')
              }}
              placeholder={t('profile:fields.name')}
              disabled={submitting}
              required
              autoFocus
            />
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
              {submitting ? t('profile:changeName.changing') : t('common:buttons.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
