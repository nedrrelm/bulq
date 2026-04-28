import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { authApi } from '../api/auth'
import type { User } from '../schemas/user'
import { getErrorMessage } from '../utils/errorHandling'
import BaseModal from '../common/BaseModal'

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
    <BaseModal
      isOpen={true}
      onClose={onClose}
      title={t('profile:changeName.title')}
      error={error}
      submitButton={{
        text: submitting ? t('profile:changeName.changing') : t('common:buttons.save'),
        onClick: handleSubmit,
        loading: submitting,
        disabled: submitting
      }}
    >
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
    </BaseModal>
  )
}
