import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import '../styles/components/NewRunPopup.css'
import { storesApi, runsApi } from '../api'
import type { Store } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import NewStorePopup from './NewStorePopup'
import { getErrorMessage } from '../utils/errorHandling'
import { logger } from '../utils/logger'

interface NewRunPopupProps {
  groupId: string
  onClose: () => void
  onSuccess: () => void
}

export default function NewRunPopup({ groupId, onClose, onSuccess }: NewRunPopupProps) {
  const { t } = useTranslation()
  const [stores, setStores] = useState<Store[]>([])
  const [selectedStoreId, setSelectedStoreId] = useState('')
  const [comment, setComment] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showNewStorePopup, setShowNewStorePopup] = useState(false)
  const overlayRef = useRef<HTMLDivElement>(null)
  const selectRef = useRef<HTMLSelectElement>(null)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

  useEffect(() => {
    const fetchStores = async () => {
      try {
        const data = await storesApi.getStores()
        const storesArray = Array.isArray(data) ? data : []
        setStores(storesArray)

        // Auto-select first store if available
        if (storesArray.length > 0 && storesArray[0]) {
          setSelectedStoreId(storesArray[0].id)
        }

        // Focus the select after stores are loaded
        setTimeout(() => selectRef.current?.focus(), 0)
      } catch (err) {
        logger.error('Error fetching stores:', err)
        setError(getErrorMessage(err, t('run.errors.loadStoresFailed')))
        setStores([])
      }
    }

    fetchStores()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedStoreId) {
      setError(t('run.validation.storeRequired'))
      return
    }

    setLoading(true)
    setError('')

    try {
      await runsApi.createRun({
        group_id: groupId,
        store_id: selectedStoreId,
        comment: comment.trim() || undefined
      })
      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, t('run.errors.createFailed')))
    } finally {
      setLoading(false)
    }
  }

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
  }

  const handleNewStoreSuccess = (newStore: Store) => {
    setShowNewStorePopup(false)
    // Add the new store to the list and select it
    setStores([...stores, newStore])
    setSelectedStoreId(newStore.id)
  }

  return (
    <div className="modal-overlay" onClick={handleOverlayClick} tabIndex={-1} ref={overlayRef}>
      <div ref={modalRef} className="modal modal-sm new-run-popup" onClick={(e) => e.stopPropagation()}>
        <h3>{t('run.create.title')}</h3>
        <p className="popup-description">{t('run.create.description')}</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="store" className="form-label">{t('run.fields.store')}</label>
            <select
              id="store"
              className="form-input"
              value={selectedStoreId}
              onChange={(e) => setSelectedStoreId(e.target.value)}
              disabled={loading || stores.length === 0}
              required
              ref={selectRef}
            >
              {stores.length === 0 && <option value="">{t('run.create.noStoresAvailable')}</option>}
              {Array.isArray(stores) && stores.map(store => (
                <option key={store.id} value={store.id}>
                  {store.name}
                </option>
              ))}
            </select>
            {stores.length === 0 && (
              <button
                type="button"
                onClick={() => setShowNewStorePopup(true)}
                className="btn btn-primary btn-sm create-store-button"
              >
                {t('run.actions.createNewStore')}
              </button>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="comment" className="form-label">{t('run.fields.comment')}</label>
            <textarea
              id="comment"
              className="form-input"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={t('run.create.commentPlaceholder')}
              disabled={loading}
              maxLength={500}
              rows={2}
            />
            <span className="char-counter">{comment.length}/500</span>
          </div>

          {stores.length > 0 && (
            <div className="form-group">
              <button
                type="button"
                onClick={() => setShowNewStorePopup(true)}
                className="btn btn-secondary btn-sm"
                disabled={loading}
              >
                {t('run.actions.createNewStore')}
              </button>
            </div>
          )}

          <div className="button-group">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="btn btn-secondary btn-md cancel-button"
            >
              {t('common.buttons.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading || !selectedStoreId}
              className="btn btn-success btn-md submit-button"
            >
              {loading ? t('run.actions.creating') : t('run.actions.createRun')}
            </button>
          </div>
        </form>
      </div>

      {showNewStorePopup && (
        <NewStorePopup
          onClose={() => setShowNewStorePopup(false)}
          onSuccess={handleNewStoreSuccess}
        />
      )}
    </div>
  )
}
