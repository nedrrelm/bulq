import { useState, useRef } from 'react'
import { adminApi, type AdminStore } from '../api/admin'
import type { ApiError } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { validateLength, validateAlphanumeric, sanitizeString } from '../utils/validation'
import { useConfirm } from '../hooks/useConfirm'
import ConfirmDialog from './ConfirmDialog'

interface EditStorePopupProps {
  store: AdminStore
  onClose: () => void
  onSuccess: () => void
}

const MAX_LENGTH = 100
const MIN_LENGTH = 2

export default function EditStorePopup({ store, onClose, onSuccess }: EditStorePopupProps) {
  const [storeName, setStoreName] = useState(store.name)
  const [address, setAddress] = useState(store.address || '')
  const [chain, setChain] = useState(store.chain || '')
  const [mergeTargetId, setMergeTargetId] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

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

    const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'', 'Store name', true)
    if (!alphanumericValidation.isValid) {
      setError(alphanumericValidation.error || 'Store name contains invalid characters')
      return false
    }

    return true
  }

  const handleNameChange = (value: string) => {
    const sanitized = sanitizeString(value, MAX_LENGTH)
    setStoreName(sanitized)
    setError('')
  }

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateStoreName(storeName)) {
      return
    }

    try {
      setSubmitting(true)
      setError('')

      await adminApi.updateStore(store.id, {
        name: storeName.trim(),
        address: address.trim() || null,
        chain: chain.trim() || null,
        opening_hours: null, // Not editing opening hours in this version
      })

      onSuccess()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to update store')
      setSubmitting(false)
    }
  }

  const handleMerge = async () => {
    if (!mergeTargetId.trim()) {
      setError('Please enter a target store ID')
      return
    }

    try {
      setSubmitting(true)
      const response = await adminApi.mergeStores(store.id, mergeTargetId.trim())
      alert(`${response.message}\nAffected records: ${response.affected_records}`)
      onSuccess()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to merge stores')
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    try {
      setSubmitting(true)
      const response = await adminApi.deleteStore(store.id)
      alert(response.message)
      onSuccess()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to delete store')
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal modal-scrollable" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Edit Store</h2>
        </div>

        <form onSubmit={handleUpdate}>
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
              placeholder="e.g., Costco, Sam's Club"
              disabled={submitting}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="address" className="form-label">Address</label>
            <textarea
              id="address"
              className="form-input"
              value={address}
              onChange={(e) => {
                setAddress(e.target.value)
                setError('')
              }}
              placeholder="Store address"
              disabled={submitting}
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="chain" className="form-label">Chain</label>
            <input
              id="chain"
              type="text"
              className="form-input"
              value={chain}
              onChange={(e) => {
                setChain(e.target.value)
                setError('')
              }}
              placeholder="e.g., Costco, Walmart"
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
              disabled={submitting}
            >
              {submitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>

        <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

        {/* Merge Section */}
        <div className="form-group">
          <label htmlFor="merge-target" className="form-label">Merge with Store</label>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
            Enter the ID of another store to merge this store into it. All runs and availabilities will be transferred.
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
              placeholder="Target store ID"
              disabled={submitting}
            />
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => showConfirm(
                `Merge "${store.name}" into another store? All runs will be transferred and this store will be deleted.`,
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
            Delete this store permanently. This cannot be undone and will fail if the store has associated runs.
          </p>
          <button
            type="button"
            className="btn"
            style={{ backgroundColor: 'var(--color-danger)', color: 'white' }}
            onClick={() => showConfirm(
              `Delete store "${store.name}"? This cannot be undone. The operation will fail if there are associated runs.`,
              handleDelete,
              true
            )}
            disabled={submitting}
          >
            Delete Store
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
