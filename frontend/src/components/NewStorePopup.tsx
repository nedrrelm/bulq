import { useState, useRef, useEffect } from 'react'
import { storesApi, ApiError } from '../api'
import type { Store } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { validateLength, validateAlphanumeric, sanitizeString } from '../utils/validation'

interface NewStorePopupProps {
  onClose: () => void
  onSuccess: (newStore: Store) => void
}

const MAX_LENGTH = 100
const MIN_LENGTH = 2

export default function NewStorePopup({ onClose, onSuccess }: NewStorePopupProps) {
  const [storeName, setStoreName] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [similarStores, setSimilarStores] = useState<Store[]>([])
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

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
      setError('Store name is required')
      return false
    }

    const lengthValidation = validateLength(trimmed, MIN_LENGTH, MAX_LENGTH, 'Store name')
    if (!lengthValidation.isValid) {
      setError(lengthValidation.error || 'Invalid store name')
      return false
    }

    const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'', 'Store name', true)
    if (!alphanumericValidation.isValid) {
      setError(alphanumericValidation.error || 'Store name contains invalid characters')
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
      setError(`A store named "${exactMatch.name}" already exists.`)
      return
    }

    try {
      setSubmitting(true)
      setError('')

      const newStore = await storesApi.createStore({ name: storeName.trim() })
      onSuccess(newStore)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create store')
      setSubmitting(false)
    }
  }

  // Check if there's an exact match
  const exactMatch = similarStores.find(
    s => s.name.toLowerCase() === storeName.trim().toLowerCase()
  )

  const hasNonExactSimilar = similarStores.length > 0 && !exactMatch

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add New Store</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="store-name" className="form-label">Store Name *</label>
            <input
              id="store-name"
              type="text"
              className={`form-input ${error ? 'input-error' : ''}`}
              value={storeName}
              onChange={(e) => handleNameChange(e.target.value)}
              onBlur={handleBlur}
              placeholder="e.g., Costco, Sam's Club"
              autoFocus
              disabled={submitting}
            />
            <small className="input-hint">
              Letters, numbers, spaces, and - _ & ' allowed (unicode supported)
            </small>

            {exactMatch && (
              <div className="alert alert-error" style={{ marginTop: '0.5rem' }}>
                A store named "{exactMatch.name}" already exists.
              </div>
            )}

            {hasNonExactSimilar && (
              <div className="alert" style={{ marginTop: '0.5rem', backgroundColor: '#fff3cd', color: '#856404', border: '1px solid #ffc107' }}>
                <strong>Similar stores found:</strong>
                <ul style={{ marginTop: '0.5rem', marginBottom: 0, paddingLeft: '1.5rem' }}>
                  {similarStores.map(store => (
                    <li key={store.id}>{store.name}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Adding...' : 'Add Store'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
