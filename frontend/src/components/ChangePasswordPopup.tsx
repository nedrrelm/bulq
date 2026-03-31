import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { authApi } from '../api/auth'
import { getErrorMessage } from '../utils/errorHandling'
import BaseModal from './BaseModal'

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
    <BaseModal
      isOpen={true}
      onClose={onClose}
      title={t('profile:changePassword.title')}
      error={error}
      submitButton={{
        text: submitting ? t('profile:changePassword.changing') : t('common:buttons.save'),
        onClick: handleSubmit,
        loading: submitting,
        disabled: submitting
      }}
    >
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
    </BaseModal>
  )
}
