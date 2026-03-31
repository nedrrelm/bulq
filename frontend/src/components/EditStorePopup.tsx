import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { adminApi, type AdminStore } from '../api/admin'
import { validateLength, validateAlphanumeric, sanitizeString } from '../utils/validation'
import { useConfirm } from '../hooks/useConfirm'
import ConfirmDialog from './ConfirmDialog'
import { getErrorMessage } from '../utils/errorHandling'
import BaseModal from './BaseModal'
import { translateSuccess } from '../utils/translation'

interface EditStorePopupProps {
  store: AdminStore
  onClose: () => void
  onSuccess: () => void
}

const MAX_LENGTH = 100
const MIN_LENGTH = 2

export default function EditStorePopup({ store, onClose, onSuccess }: EditStorePopupProps) {
  const { t } = useTranslation(['admin', 'common'])
  const [storeName, setStoreName] = useState(store.name)
  const [address, setAddress] = useState(store.address || '')
  const [chain, setChain] = useState(store.chain || '')
  const [mergeTargetId, setMergeTargetId] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()


  const validateStoreName = (value: string): boolean => {
    setError('')

    const trimmed = value.trim()

    if (trimmed.length === 0) {
      setError(t('admin:edit.store.errors.nameRequired'))
      return false
    }

    const lengthValidation = validateLength(trimmed, MIN_LENGTH, MAX_LENGTH, 'Store name')
    if (!lengthValidation.isValid) {
      setError(lengthValidation.error || t('admin:edit.store.errors.invalidName'))
      return false
    }

    const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'', 'Store name', true)
    if (!alphanumericValidation.isValid) {
      setError(alphanumericValidation.error || t('admin:edit.store.errors.invalidCharacters'))
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
      setError(getErrorMessage(err, 'Failed to update store'))
      setSubmitting(false)
    }
  }

  const handleMerge = async () => {
    if (!mergeTargetId.trim()) {
      setError(t('admin:edit.store.errors.mergeTargetRequired'))
      return
    }

    try {
      setSubmitting(true)
      const response = await adminApi.mergeStores(store.id, mergeTargetId.trim())
      const successMsg = translateSuccess(response.code, response.details)
      alert(`${successMsg}\n${t('admin:edit.affectedRecords')}: ${response.affected_records}`)
      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, t('admin:edit.store.errors.mergeFailed')))
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    try {
      setSubmitting(true)
      const response = await adminApi.deleteStore(store.id)
      alert(translateSuccess(response.code, response.details))
      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to delete store'))
      setSubmitting(false)
    }
  }

  return (
    <>
      <BaseModal
        isOpen={true}
        onClose={onClose}
        title={t('admin:edit.store.title')}
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
            <label htmlFor="store-name" className="form-label">{t('admin:edit.store.fields.name')} *</label>
            <input
              id="store-name"
              type="text"
              className={`form-input ${error ? 'input-error' : ''}`}
              value={storeName}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder={t('admin:edit.store.placeholders.name')}
              disabled={submitting}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="address" className="form-label">{t('admin:edit.store.fields.address')}</label>
            <textarea
              id="address"
              className="form-input"
              value={address}
              onChange={(e) => {
                setAddress(e.target.value)
                setError('')
              }}
              placeholder={t('admin:edit.store.placeholders.address')}
              disabled={submitting}
              rows={3}
            />
          </div>

          <div className="form-group">
            <label htmlFor="chain" className="form-label">{t('admin:edit.store.fields.chain')}</label>
            <input
              id="chain"
              type="text"
              className="form-input"
              value={chain}
              onChange={(e) => {
                setChain(e.target.value)
                setError('')
              }}
              placeholder={t('admin:edit.store.placeholders.chain')}
              disabled={submitting}
            />
          </div>

        <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

        {/* Merge Section */}
        <div className="form-group">
          <label htmlFor="merge-target" className="form-label">{t('admin:edit.store.mergeTitle')}</label>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
            {t('admin:edit.store.mergeDescription')}
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
              placeholder={t('admin:edit.store.mergePlaceholder')}
              disabled={submitting}
            />
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => showConfirm(
                t('admin:edit.store.mergeConfirm', { name: store.name }),
                handleMerge
              )}
              disabled={submitting || !mergeTargetId.trim()}
            >
              {t('admin:edit.store.mergeButton')}
            </button>
          </div>
        </div>

        <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

        {/* Delete Section */}
        <div className="form-group">
          <label className="form-label" style={{ color: 'var(--color-danger)' }}>{t('admin:edit.dangerZone')}</label>
          <p style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', marginBottom: '0.5rem' }}>
            {t('admin:edit.store.deleteWarning')}
          </p>
          <button
            type="button"
            className="btn"
            style={{ backgroundColor: 'var(--color-danger)', color: 'white' }}
            onClick={() => showConfirm(
              t('admin:edit.store.deleteConfirm', { name: store.name }),
              handleDelete,
              { danger: true }
            )}
            disabled={submitting}
          >
            {t('admin:edit.store.deleteButton')}
          </button>
        </div>
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
