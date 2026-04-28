import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { groupsApi } from '../api'
import type { Group } from '../api'
import { getErrorMessage } from '../utils/errorHandling'
import BaseModal from '../common/BaseModal'
import { useFormValidation, validators, sanitizeString } from '../hooks/useFormValidation'

interface NewGroupPopupProps {
  onClose: () => void
  onSuccess: (newGroup: Group) => void
}

const MAX_LENGTH = 100
const MIN_LENGTH = 2

export default function NewGroupPopup({ onClose, onSuccess }: NewGroupPopupProps) {
  const { t } = useTranslation(['common', 'groups'])
  const [groupName, setGroupName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState('')

  const { error, validate, handleChange, handleBlur } = useFormValidation({
    value: groupName,
    onChange: setGroupName,
    validators: [
      validators.required(t('groups:validation.nameRequired')),
      validators.length(MIN_LENGTH, MAX_LENGTH, t('groups:fields.name')),
      validators.alphanumeric('- _&\'', t('groups:fields.name'))
    ],
    sanitize: (v) => sanitizeString(v, MAX_LENGTH),
    validateOnBlur: true
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    try {
      setSubmitting(true)
      setServerError('')

      const newGroup = await groupsApi.createGroup({ name: groupName.trim() })
      onSuccess(newGroup)
    } catch (err) {
      setServerError(getErrorMessage(err, 'Failed to create group'))
      setSubmitting(false)
    }
  }

  return (
    <BaseModal
      isOpen={true}
      onClose={onClose}
      title={t('groups:create.title')}
      error={error || serverError}
      submitButton={{
        text: submitting ? t('groups:create.submitting') : t('groups:create.submit'),
        onClick: handleSubmit,
        loading: submitting,
        disabled: submitting
      }}
    >
      <div className="form-group">
        <label htmlFor="group-name" className="form-label">{t('groups:fields.name')} *</label>
        <input
          id="group-name"
          type="text"
          className={`form-input ${error ? 'input-error' : ''}`}
          value={groupName}
          onChange={(e) => handleChange(e.target.value)}
          onBlur={handleBlur}
          placeholder={t('groups:create.namePlaceholder')}
          autoFocus
          disabled={submitting}
        />
        <small className="input-hint">
          {t('groups:validation.nameHint')}
        </small>
      </div>
    </BaseModal>
  )
}
