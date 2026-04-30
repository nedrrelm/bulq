import { useState, useEffect, useRef, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import '../../styles/components/NewRunPopup.css'
import { runsApi } from '../../api'
import type { Store } from '../../api'
import NewStorePopup from './NewStorePopup'
import { getErrorMessage } from '../../utils/errorHandling'
import BaseModal from '../common/BaseModal'
import { useStores, storeKeys } from '../../hooks/queries'

interface NewRunPopupProps {
  groupId: string
  onClose: () => void
  onSuccess: () => void
}

export default function NewRunPopup({ groupId, onClose, onSuccess }: NewRunPopupProps) {
  const { t } = useTranslation(['common', 'run'])
  const { data: storesData, error: storesError } = useStores()
  const stores = useMemo(() => Array.isArray(storesData) ? storesData : [], [storesData])
  const [selectedStoreId, setSelectedStoreId] = useState('')
  const [comment, setComment] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showNewStorePopup, setShowNewStorePopup] = useState(false)
  const selectRef = useRef<HTMLSelectElement>(null)

  // Auto-select first store when stores load
  useEffect(() => {
    if (stores.length > 0 && !selectedStoreId && stores[0]) {
      setSelectedStoreId(stores[0].id)
      setTimeout(() => selectRef.current?.focus(), 0)
    }
  }, [stores, selectedStoreId])

  // Map store loading error
  useEffect(() => {
    if (storesError) {
      setError(getErrorMessage(storesError, t('run:errors.loadStoresFailed')))
    }
  }, [storesError, t])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedStoreId) {
      setError(t('run:validation.storeRequired'))
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
      setError(getErrorMessage(err, t('run:errors.createFailed')))
    } finally {
      setLoading(false)
    }
  }

  const queryClient = useQueryClient()

  const handleNewStoreSuccess = (newStore: Store) => {
    setShowNewStorePopup(false)
    // Invalidate stores query so the list refreshes, and select the new store
    queryClient.invalidateQueries({ queryKey: storeKeys.list() })
    setSelectedStoreId(newStore.id)
  }

  return (
    <>
      <BaseModal
        isOpen={true}
        onClose={onClose}
        size="sm"
        className="new-run-popup"
        showHeader={false}
        error={error}
        submitButton={{
          text: loading ? t('run:actions.creating') : t('run:actions.createRun'),
          onClick: handleSubmit,
          variant: 'success',
          loading: loading,
          disabled: loading || !selectedStoreId
        }}
      >
        <h3>{t('run:create.title')}</h3>
        <p className="popup-description">{t('run:create.description')}</p>

        <div className="form-group">
          <label htmlFor="store" className="form-label">{t('run:fields.store')}</label>
          <select
            id="store"
            className="form-input"
            value={selectedStoreId}
            onChange={(e) => setSelectedStoreId(e.target.value)}
            disabled={loading || stores.length === 0}
            required
            ref={selectRef}
          >
            {stores.length === 0 && <option value="">{t('run:create.noStoresAvailable')}</option>}
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
              {t('run:actions.createNewStore')}
            </button>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="comment" className="form-label">{t('run:fields.comment')}</label>
          <textarea
            id="comment"
            className="form-input"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={t('run:create.commentPlaceholder')}
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
              {t('run:actions.createNewStore')}
            </button>
          </div>
        )}
      </BaseModal>

      {showNewStorePopup && (
        <NewStorePopup
          onClose={() => setShowNewStorePopup(false)}
          onSuccess={handleNewStoreSuccess}
        />
      )}
    </>
  )
}
