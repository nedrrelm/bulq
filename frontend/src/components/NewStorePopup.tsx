import { useState, useRef } from 'react'
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
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

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

    const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'', 'Store name')
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

  const charCount = storeName.length

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
              Use letters, numbers, spaces, and - _ & '
            </small>
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
