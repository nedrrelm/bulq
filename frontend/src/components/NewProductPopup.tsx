import { useState, useEffect, useRef } from 'react'
import { storesApi, productsApi, ApiError } from '../api'
import type { Store } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { validateLength, validateAlphanumeric, validateDecimal, sanitizeString } from '../utils/validation'
import { useConfirm } from '../hooks/useConfirm'
import ConfirmDialog from './ConfirmDialog'

interface NewProductPopupProps {
  onClose: () => void
  onSuccess: () => void
  initialStoreId?: string
}

const MAX_NAME_LENGTH = 100
const MIN_NAME_LENGTH = 2

export default function NewProductPopup({ onClose, onSuccess, initialStoreId }: NewProductPopupProps) {
  const [productName, setProductName] = useState('')
  const [brand, setBrand] = useState('')
  const [unit, setUnit] = useState('')
  const [storeId, setStoreId] = useState(initialStoreId || '')
  const [price, setPrice] = useState('')
  const [stores, setStores] = useState<Store[]>([])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [loadingStores, setLoadingStores] = useState(true)
  const modalRef = useRef<HTMLDivElement>(null)
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

  useModalFocusTrap(modalRef, true, onClose)

  useEffect(() => {
    const fetchStores = async () => {
      try {
        const storesData = await storesApi.getStores()
        setStores(Array.isArray(storesData) ? storesData : [])
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Failed to load stores')
        setStores([])
      } finally {
        setLoadingStores(false)
      }
    }

    fetchStores()
  }, [])

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

    const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'(),.', 'Product name', true)
    if (!alphanumericValidation.isValid) {
      setError(alphanumericValidation.error || 'Product name contains invalid characters')
      return false
    }

    return true
  }

  const validatePrice = (value: string): boolean => {
    // Price is optional
    if (!value.trim()) {
      return true
    }

    const priceValidation = validateDecimal(value, 0.01, 999999.99, 2, 'Price')
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
    setPrice(value)
    setError('')
  }

  const submitProduct = async () => {
    try {
      setSubmitting(true)

      await productsApi.createProduct({
        name: productName.trim(),
        brand: brand.trim() || null,
        unit: unit.trim() || null,
        store_id: storeId || null,
        price: price.trim() ? parseFloat(price) : null
      })

      onSuccess()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create product')
      setSubmitting(false)
    }
  }

  const checkStoreAndPrice = () => {
    // Nudge to add price if store is selected but no price
    if (storeId && !price.trim()) {
      showConfirm(
        'Consider adding a price for this product at the selected store. Continue without price?',
        submitProduct
      )
      return
    }

    // If all validations pass, submit directly
    submitProduct()
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setError('')

    if (!validateProductName(productName)) {
      return
    }

    if (!validatePrice(price)) {
      return
    }

    // Warn if no store selected
    if (!storeId) {
      showConfirm(
        'You haven\'t selected a store. You can add store availability later. Continue?',
        checkStoreAndPrice
      )
      return
    }

    // Check for price if store is selected
    checkStoreAndPrice()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal modal-scrollable" onClick={(e) => e.stopPropagation()}>
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
            <label htmlFor="product-name" className="form-label">Product Name *</label>
            <input
              id="product-name"
              type="text"
              className={`form-input ${error ? 'input-error' : ''}`}
              value={productName}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="e.g., Organic Olive Oil"
              disabled={submitting}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="brand" className="form-label">Brand</label>
              <input
                id="brand"
                type="text"
                className="form-input"
                value={brand}
                onChange={(e) => {
                  setBrand(e.target.value)
                  setError('')
                }}
                placeholder="e.g., Kirkland"
                disabled={submitting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="unit" className="form-label">Unit</label>
              <input
                id="unit"
                type="text"
                className="form-input"
                value={unit}
                onChange={(e) => {
                  setUnit(e.target.value)
                  setError('')
                }}
                placeholder="kg, lb, each"
                disabled={submitting}
              />
            </div>
          </div>

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
            >
              <option value="">Select a store...</option>
              {Array.isArray(stores) && stores.map((store) => (
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
            <label htmlFor="price" className="form-label">Price ($)</label>
            <input
              id="price"
              type="text"
              inputMode="decimal"
              className="form-input"
              value={price}
              onChange={(e) => handlePriceChange(e.target.value)}
              placeholder="0.00"
              disabled={submitting}
            />
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

      {confirmState && (
        <ConfirmDialog
          message={confirmState.message}
          onConfirm={handleConfirm}
          onCancel={hideConfirm}
          danger={confirmState.danger}
        />
      )}
    </div>
  )
}
