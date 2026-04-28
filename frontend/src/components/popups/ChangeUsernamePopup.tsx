import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { authApi } from '../api/auth'
import type { User } from '../schemas/user'
import { getErrorMessage } from '../utils/errorHandling'
import BaseModal from '../common/BaseModal'
import { useFormValidation, validators } from '../hooks/useFormValidation'

interface ChangeUsernamePopupProps {
  onClose: () => void
  onSuccess: (updatedUser: User) => void
}

export default function ChangeUsernamePopup({ onClose, onSuccess }: ChangeUsernamePopupProps) {
  const { t } = useTranslation(['common', 'profile'])
  const [newUsername, setNewUsername] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState('')

  const { error, validate } = useFormValidation({
    value: newUsername,
    onChange: setNewUsername,
    validators: [
      validators.minLength(3, t('profile:fields.username')),
      validators.pattern(/^[a-zA-Z0-9_-]+$/, t('profile:validation.usernameInvalidChars'))
    ]
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    try {
      setSubmitting(true)
      const updatedUser = await authApi.changeUsername(currentPassword, newUsername)
      onSuccess(updatedUser)
    } catch (err) {
      setServerError(getErrorMessage(err, 'Failed to change username'))
      setSubmitting(false)
    }
  }

  return (
    <BaseModal
      isOpen={true}
      onClose={onClose}
      title={t('profile:changeUsername.title')}
      error={error || serverError}
      submitButton={{
        text: submitting ? t('profile:changeUsername.changing') : t('common:buttons.save'),
        onClick: handleSubmit,
        loading: submitting,
        disabled: submitting
      }}
    >
      <div className="form-group">
        <label htmlFor="new-username" className="form-label">{t('profile:fields.username')} *</label>
        <input
          id="new-username"
          type="text"
          className="form-input"
          value={newUsername}
          onChange={(e) => {
            setNewUsername(e.target.value)
            setServerError('')
          }}
          placeholder={t('profile:fields.username')}
          disabled={submitting}
          minLength={3}
          maxLength={50}
          required
          autoFocus
        />
        <small className="input-hint">
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
            setServerError('')
          }}
          placeholder={t('profile:fields.currentPassword')}
          disabled={submitting}
          required
        />
      </div>
    </BaseModal>
  )
}
