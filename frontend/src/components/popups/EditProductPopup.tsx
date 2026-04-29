import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { adminApi, type AdminProduct } from '../../api/admin'
import { validateLength, validateAlphanumeric, sanitizeString } from '../../utils/validation'
import { useConfirm } from '../../hooks/useConfirm'
import ConfirmDialog from '../common/ConfirmDialog'
import { getErrorMessage } from '../../utils/errorHandling'
import BaseModal from '../common/BaseModal'
import { AdminMergeSection } from '../admin/AdminMergeSection'
import { AdminDeleteSection } from '../admin/AdminDeleteSection'

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
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

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

  return (
    <>
      <BaseModal
        isOpen={true}
        onClose={onClose}
        title={t('admin:edit.product.title')}
        error={error}
        size="scrollable"
        submitButton={{
          text: submitting ? t('common:saving') : t('common:saveChanges'),
          onClick: handleUpdate,
          loading: submitting,
          disabled: submitting
        }}
      >

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

        <hr className="divider" />

        <AdminMergeSection
          entityType="product"
          entityId={product.id}
          entityName={product.name}
          mergeHandler={adminApi.mergeProducts}
          onSuccess={onSuccess}
          onError={setError}
          disabled={submitting}
          showConfirm={showConfirm}
        />

        <hr className="divider" />

        <AdminDeleteSection
          entityType="product"
          entityId={product.id}
          entityName={product.name}
          deleteHandler={adminApi.deleteProduct}
          onSuccess={onSuccess}
          onError={setError}
          disabled={submitting}
          showConfirm={showConfirm}
        />
      </BaseModal>

      {confirmState && (
        <ConfirmDialog
          message={confirmState.message}
          onConfirm={handleConfirm}
          onCancel={hideConfirm}
          danger={confirmState.danger}
        />
      )}
    </>
  )
}
