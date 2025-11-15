import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
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
  const { t } = useTranslation(['admin', 'common'])
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
      setError(t('admin:edit.product.errors.nameRequired'))
      return false
    }

    const lengthValidation = validateLength(trimmed, MIN_NAME_LENGTH, MAX_NAME_LENGTH, 'Product name')
    if (!lengthValidation.isValid) {
      setError(lengthValidation.error || t('admin:edit.product.errors.invalidName'))
      return false
    }

    const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'(),.', 'Product name', true)
    if (!alphanumericValidation.isValid) {
      setError(alphanumericValidation.error || t('admin:edit.product.errors.invalidCharacters'))
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
      setError(t('admin:edit.product.errors.mergeTargetRequired'))
      return
    }

    try {
      setSubmitting(true)
      const response = await adminApi.mergeProducts(product.id, mergeTargetId.trim())
      const successMsg = translateSuccess(response.code, response.details)
      alert(`${successMsg}\n${t('admin:edit.affectedRecords')}: ${response.affected_records}`)
      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, t('admin:edit.product.errors.mergeFailed')))
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
          <h2>{t('admin:edit.product.title')}</h2>
        </div>

        <form onSubmit={handleUpdate}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="product-name" className="form-label">{t('admin:edit.product.fields.name')} *</label>
            <input
              id="product-name"
              type="text"
              className={`form-input ${error ? 'input-error' : ''}`}
              value={productName}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder={t('admin:edit.product.placeholders.name')}
              disabled={submitting}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="brand" className="form-label">{t('admin:edit.product.fields.brand')}</label>
              <input
                id="brand"
                type="text"
                className="form-input"
                value={brand}
                onChange={(e) => {
                  setBrand(e.target.value)
                  setError('')
                }}
                placeholder={t('admin:edit.product.placeholders.brand')}
                disabled={submitting}
              />
            </div>

            <div className="form-group">
              <label htmlFor="unit" className="form-label">{t('admin:edit.product.fields.unit')}</label>
              <input
                id="unit"
                type="text"
                className="form-input"
                value={unit}
                onChange={(e) => {
                  setUnit(e.target.value)
                  setError('')
                }}
                placeholder={t('admin:edit.product.placeholders.unit')}
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
              {t('common:cancel')}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? t('common:saving') : t('common:saveChanges')}
            </button>
          </div>
        </form>

        <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

        {/* Merge Section */}
        <div className="form-group">
          <label htmlFor="merge-target" className="form-label">{t('admin:edit.product.mergeTitle')}</label>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
            {t('admin:edit.product.mergeDescription')}
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
              placeholder={t('admin:edit.product.mergePlaceholder')}
              disabled={submitting}
            />
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => showConfirm(
                t('admin:edit.product.mergeConfirm', { name: product.name }),
                handleMerge
              )}
              disabled={submitting || !mergeTargetId.trim()}
            >
              {t('admin:edit.product.mergeButton')}
            </button>
          </div>
        </div>

        <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

        {/* Delete Section */}
        <div className="form-group">
          <label className="form-label" style={{ color: 'var(--color-danger)' }}>{t('admin:edit.dangerZone')}</label>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
            {t('admin:edit.product.deleteWarning')}
          </p>
          <button
            type="button"
            className="btn"
            style={{ backgroundColor: 'var(--color-danger)', color: 'white' }}
            onClick={() => showConfirm(
              t('admin:edit.product.deleteConfirm', { name: product.name }),
              handleDelete,
              { danger: true }
            )}
            disabled={submitting}
          >
            {t('admin:edit.product.deleteButton')}
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
