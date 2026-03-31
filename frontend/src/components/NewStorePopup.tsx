import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { storesApi } from '../api'
import type { Store } from '../api'
import { getErrorMessage } from '../utils/errorHandling'
import BaseModal from './BaseModal'
import { useFormValidation, validators, sanitizeString } from '../hooks/useFormValidation'

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
  const [similarStores, setSimilarStores] = useState<Store[]>([])

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
  useEffect(() => {
    const checkSimilar = async () => {
      const trimmed = storeName.trim()

      // Only check if we have at least MIN_LENGTH characters
      if (trimmed.length < MIN_LENGTH) {
        setSimilarStores([])
        return
      }

      try {
        const similar = await storesApi.checkSimilar(trimmed)
        setSimilarStores(similar)
      } catch (err) {
        // Silently fail - this is a nice-to-have feature
        setSimilarStores([])
      }
    }

    // Debounce the API call
    const timeoutId = setTimeout(checkSimilar, 300)
    return () => clearTimeout(timeoutId)
  }, [storeName])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    // Check for exact match
    const exactMatch = similarStores.find(
      s => s.name.toLowerCase() === storeName.trim().toLowerCase()
    )

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

  // Check if there's an exact match
  const exactMatch = similarStores.find(
    s => s.name.toLowerCase() === storeName.trim().toLowerCase()
  )

  const hasNonExactSimilar = similarStores.length > 0 && !exactMatch

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
