import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { storesApi } from '../api'
import type { Store } from '../api'
import { validateLength, validateAlphanumeric, sanitizeString } from '../utils/validation'
import { getErrorMessage } from '../utils/errorHandling'
import BaseModal from './BaseModal'

interface NewStorePopupProps {
  onClose: () => void
  onSuccess: (newStore: Store) => void
}

const MAX_LENGTH = 100
const MIN_LENGTH = 2

export default function NewStorePopup({ onClose, onSuccess }: NewStorePopupProps) {
  const { t } = useTranslation(['common', 'store'])
  const [storeName, setStoreName] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [similarStores, setSimilarStores] = useState<Store[]>([])

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

  const validateStoreName = (value: string): boolean => {
    setError('')

    const trimmed = value.trim()

    if (trimmed.length === 0) {
      setError(t('store:validation.nameRequired'))
      return false
    }

    const lengthValidation = validateLength(trimmed, MIN_LENGTH, MAX_LENGTH, t('store:fields.name'))
    if (!lengthValidation.isValid) {
      setError(lengthValidation.error || t('store:validation.nameInvalid'))
      return false
    }

    const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'', t('store:fields.name'), true)
    if (!alphanumericValidation.isValid) {
      setError(alphanumericValidation.error || t('store:validation.nameInvalidCharacters'))
      return false
    }

    return true
  }

  const handleNameChange = (value: string) => {
    // Limit input to max length
    const sanitized = sanitizeString(value, MAX_LENGTH)
    setStoreName(sanitized)
    setError('') // Clear error on change
  }

  const handleBlur = () => {
    if (storeName.trim()) {
      validateStoreName(storeName)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateStoreName(storeName)) {
      return
    }

    // Check for exact match
    const exactMatch = similarStores.find(
      s => s.name.toLowerCase() === storeName.trim().toLowerCase()
    )

    if (exactMatch) {
      setError(t('store:validation.alreadyExists', { name: exactMatch.name }))
      return
    }

    try {
      setSubmitting(true)
      setError('')

      const newStore = await storesApi.createStore({ name: storeName.trim() })
      onSuccess(newStore)
    } catch (err) {
      setError(getErrorMessage(err, t('store:errors.createFailed')))
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
      error={error}
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
          onChange={(e) => handleNameChange(e.target.value)}
          onBlur={handleBlur}
          placeholder={t('store:fields.namePlaceholder')}
          autoFocus
          disabled={submitting}
        />
        <small className="input-hint">
          {t('store:validation.nameHint')}
        </small>

        {exactMatch && (
          <div className="alert alert-error" style={{ marginTop: '0.5rem' }}>
            {t('store:validation.alreadyExists', { name: exactMatch.name })}
          </div>
        )}

        {hasNonExactSimilar && (
          <div className="alert" style={{ marginTop: '0.5rem', backgroundColor: '#fff3cd', color: '#856404', border: '1px solid #ffc107' }}>
            <strong>{t('store:validation.similarFound')}:</strong>
            <ul style={{ marginTop: '0.5rem', marginBottom: 0, paddingLeft: '1.5rem' }}>
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
