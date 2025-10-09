import { useState, useEffect, useRef } from 'react'
import { storesApi, productsApi, ApiError } from '../api'
import type { Store } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { validateLength, validateAlphanumeric, validateDecimal, sanitizeString } from '../utils/validation'

interface NewProductPopupProps {
  onClose: () => void
  onSuccess: () => void
}

const MAX_NAME_LENGTH = 100
const MIN_NAME_LENGTH = 2

export default function NewProductPopup({ onClose, onSuccess }: NewProductPopupProps) {
  const [productName, setProductName] = useState('')
  const [storeId, setStoreId] = useState('')
  const [basePrice, setBasePrice] = useState('')
  const [stores, setStores] = useState<Store[]>([])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [loadingStores, setLoadingStores] = useState(true)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef)

  useEffect(() => {
    const fetchStores = async () => {
      try {
        const storesData = await storesApi.getStores()
        setStores(storesData)
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Failed to load stores')
      } finally {
        setLoadingStores(false)
      }
    }

    fetchStores()
  }, [])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  const validateProductName = (value: string): boolean => {
    const trimmed = value.trim()

    if (trimmed.length === 0) {
      setError('Product name is required')
      return false
    }

    const lengthValidation = validateLength(trimmed, MIN_NAME_LENGTH, MAX_NAME_LENGTH, 'Product name')
    if (!lengthValidation.isValid) {
      setError(lengthValidation.error || 'Invalid product name')
      return false
    }

    const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'(),.', 'Product name')
    if (!alphanumericValidation.isValid) {
      setError(alphanumericValidation.error || 'Product name contains invalid characters')
      return false
    }

    return true
  }

  const validatePrice = (value: string): boolean => {
    if (!value.trim()) {
      setError('Base price is required')
      return false
    }

    const priceValidation = validateDecimal(value, 0.01, 999999.99, 2, 'Base price')
    if (!priceValidation.isValid) {
      setError(priceValidation.error || 'Invalid price')
      return false
    }

    return true
  }

  const handleNameChange = (value: string) => {
    const sanitized = sanitizeString(value, MAX_NAME_LENGTH)
    setProductName(sanitized)
    setError('')
  }

  const handlePriceChange = (value: string) => {
    // Allow only numbers and decimal point
    if (value && !/^\d*\.?\d{0,2}$/.test(value)) {
      return
    }
    setBasePrice(value)
    setError('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setError('')

    if (!storeId) {
      setError('Please select a store')
      return
    }

    if (!validateProductName(productName)) {
      return
    }

    if (!validatePrice(basePrice)) {
      return
    }

    try {
      setSubmitting(true)

      await productsApi.createProduct({
        store_id: storeId,
        name: productName.trim(),
        base_price: parseFloat(basePrice)
      })

      onSuccess()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create product')
      setSubmitting(false)
    }
  }

  const charCount = productName.length
  const isOverLimit = charCount > MAX_NAME_LENGTH

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add New Product</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="store-select" className="form-label">Store</label>
            <select
              id="store-select"
              className="form-input"
              value={storeId}
              onChange={(e) => {
                setStoreId(e.target.value)
                setError('')
              }}
              disabled={submitting || loadingStores}
              required
            >
              <option value="">Select a store...</option>
              {stores.map((store) => (
                <option key={store.id} value={store.id}>
                  {store.name}
                </option>
              ))}
            </select>
            {loadingStores && (
              <small className="input-hint">Loading stores...</small>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="product-name" className="form-label">Product Name</label>
            <input
              id="product-name"
              type="text"
              className={`form-input ${error ? 'input-error' : ''}`}
              value={productName}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="e.g., Organic Olive Oil (2L)"
              disabled={submitting}
              required
            />
            <div className="input-footer">
              <span className={`char-counter ${isOverLimit ? 'over-limit' : ''}`}>
                {charCount}/{MAX_NAME_LENGTH}
              </span>
            </div>
            <small className="input-hint">
              Use letters, numbers, spaces, and - _ & ' ( ) , .
            </small>
          </div>

          <div className="form-group">
            <label htmlFor="base-price" className="form-label">Base Price ($)</label>
            <input
              id="base-price"
              type="text"
              inputMode="decimal"
              className="form-input"
              value={basePrice}
              onChange={(e) => handlePriceChange(e.target.value)}
              placeholder="0.00"
              disabled={submitting}
              required
            />
            <small className="input-hint">
              Enter the regular price for this product
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
              disabled={submitting || loadingStores}
            >
              {submitting ? 'Adding...' : 'Add Product'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
