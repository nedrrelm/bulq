import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { storesApi } from '../api'
import type { Store } from '../api'
import { getErrorMessage } from '../utils/errorHandling'
import BaseModal from '../common/BaseModal'
import { useFormValidation, validators, sanitizeString } from '../hooks/useFormValidation'
import { useSimilarEntities } from '../hooks/useSimilarEntities'

interface NewStorePopupProps {
  onClose: () => void
  onSuccess: (newStore: Store) => void
}

const MAX_LENGTH = 100
const MIN_LENGTH = 2

export default function NewStorePopup({ onClose, onSuccess }: NewStorePopupProps) {
  const { t } = useTranslation(['common', 'store'])
  const [storeName, setStoreName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState('')

  const { error, validate, handleChange, handleBlur } = useFormValidation({
    value: storeName,
    onChange: setStoreName,
    validators: [
      validators.required(t('store:validation.nameRequired')),
      validators.length(MIN_LENGTH, MAX_LENGTH, t('store:fields.name')),
      validators.alphanumeric('- _&\'', t('store:fields.name'), true)
    ],
    sanitize: (v) => sanitizeString(v, MAX_LENGTH),
    validateOnBlur: true
  })

  // Check for similar stores as user types
  const { similar: similarStores, exactMatch, hasNonExactSimilar } = useSimilarEntities({
    searchValue: storeName,
    fetcher: storesApi.checkSimilar,
    minLength: MIN_LENGTH
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    // Check for exact match
    if (exactMatch) {
      setServerError(t('store:validation.alreadyExists', { name: exactMatch.name }))
      return
    }

    try {
      setSubmitting(true)
      setServerError('')

      const newStore = await storesApi.createStore({ name: storeName.trim() })
      onSuccess(newStore)
    } catch (err) {
      setServerError(getErrorMessage(err, t('store:errors.createFailed')))
      setSubmitting(false)
    }
  }

  return (
    <BaseModal
      isOpen={true}
      onClose={onClose}
      title={t('store:create.title')}
      error={error || serverError}
      submitButton={{
        text: submitting ? t('store:actions.creating') : t('store:actions.create'),
        onClick: handleSubmit,
        loading: submitting,
        disabled: submitting
      }}
    >
      <div className="form-group">
        <label htmlFor="store-name" className="form-label">{t('store:fields.name')} *</label>
        <input
          id="store-name"
          type="text"
          className={`form-input ${error ? 'input-error' : ''}`}
          value={storeName}
          onChange={(e) => handleChange(e.target.value)}
          onBlur={handleBlur}
          placeholder={t('store:fields.namePlaceholder')}
          autoFocus
          disabled={submitting}
        />
        <small className="input-hint">
          {t('store:validation.nameHint')}
        </small>

        {exactMatch && (
          <div className="alert alert-error mt-sm">
            {t('store:validation.alreadyExists', { name: exactMatch.name })}
          </div>
        )}

        {hasNonExactSimilar && (
          <div className="alert-warning mt-sm">
            <strong>{t('store:validation.similarFound')}:</strong>
            <ul className="list-compact">
              {similarStores.map(store => (
                <li key={store.id}>{store.name}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </BaseModal>
  )
}
