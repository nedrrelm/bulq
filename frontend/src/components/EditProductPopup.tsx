import { useState, useRef } from 'react'
import { adminApi, type AdminProduct } from '../api/admin'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { validateLength, validateAlphanumeric, sanitizeString } from '../utils/validation'
import { useConfirm } from '../hooks/useConfirm'
import ConfirmDialog from './ConfirmDialog'
import { getErrorMessage } from '../utils/errorHandling'
import { translateSuccess } from '../utils/translation'

interface EditProductPopupProps {
  product: AdminProduct
  onClose: () => void
  onSuccess: () => void
}

const MAX_NAME_LENGTH = 100
const MIN_NAME_LENGTH = 2

export default function EditProductPopup({ product, onClose, onSuccess }: EditProductPopupProps) {
  const [productName, setProductName] = useState(product.name)
  const [brand, setBrand] = useState(product.brand || '')
  const [unit, setUnit] = useState(product.unit || '')
  const [mergeTargetId, setMergeTargetId] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

  useModalFocusTrap(modalRef, true, onClose)

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

  const handleNameChange = (value: string) => {
    const sanitized = sanitizeString(value, MAX_NAME_LENGTH)
    setProductName(sanitized)
    setError('')
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()

    setError('')

    if (!validateProductName(productName)) {
      return
    }

    try {
      setSubmitting(true)

      const trimmedBrand = brand.trim()
      const trimmedUnit = unit.trim()

      await adminApi.updateProduct(product.id, {
        name: productName.trim(),
        brand: trimmedBrand === '' ? null : trimmedBrand,
        unit: trimmedUnit === '' ? null : trimmedUnit,
      })

      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to update product'))
      setSubmitting(false)
    }
  }

  const handleMerge = async () => {
    if (!mergeTargetId.trim()) {
      setError('Please enter a target product ID')
      return
    }

    try {
      setSubmitting(true)
      const response = await adminApi.mergeProducts(product.id, mergeTargetId.trim())
      const successMsg = translateSuccess(response.code, response.details)
      alert(`${successMsg}\nAffected records: ${response.affected_records}`)
      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to merge products'))
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    try {
      setSubmitting(true)
      const response = await adminApi.deleteProduct(product.id)
      alert(translateSuccess(response.code, response.details))
      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to delete product'))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal modal-scrollable" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Edit Product</h2>
        </div>

        <form onSubmit={handleUpdate}>
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
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>

        <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

        {/* Merge Section */}
        <div className="form-group">
          <label htmlFor="merge-target" className="form-label">Merge with Product</label>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
            Enter the ID of another product to merge this product into it. All bids and availabilities will be transferred.
          </p>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              id="merge-target"
              type="text"
              className="form-input"
              value={mergeTargetId}
              onChange={(e) => {
                setMergeTargetId(e.target.value)
                setError('')
              }}
              placeholder="Target product ID"
              disabled={submitting}
            />
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => showConfirm(
                `Merge "${product.name}" into another product? All bids will be transferred and this product will be deleted.`,
                handleMerge
              )}
              disabled={submitting || !mergeTargetId.trim()}
            >
              Merge
            </button>
          </div>
        </div>

        <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

        {/* Delete Section */}
        <div className="form-group">
          <label className="form-label" style={{ color: 'var(--color-danger)' }}>Danger Zone</label>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
            Delete this product permanently. This cannot be undone and will fail if the product has associated bids.
          </p>
          <button
            type="button"
            className="btn"
            style={{ backgroundColor: 'var(--color-danger)', color: 'white' }}
            onClick={() => showConfirm(
              `Delete product "${product.name}"? This cannot be undone. The operation will fail if there are associated bids.`,
              handleDelete,
              { danger: true }
            )}
            disabled={submitting}
          >
            Delete Product
          </button>
        </div>
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
