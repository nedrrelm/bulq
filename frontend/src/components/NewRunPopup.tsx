import { useState, useEffect, useRef } from 'react'
import '../styles/components/NewRunPopup.css'
import { storesApi, runsApi, ApiError } from '../api'
import type { Store } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import NewStorePopup from './NewStorePopup'

interface NewRunPopupProps {
  groupId: string
  onClose: () => void
  onSuccess: () => void
}

export default function NewRunPopup({ groupId, onClose, onSuccess }: NewRunPopupProps) {
  const [stores, setStores] = useState<Store[]>([])
  const [selectedStoreId, setSelectedStoreId] = useState('')
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
        setStores(data)

        // Auto-select first store if available
        if (data.length > 0 && data[0]) {
          setSelectedStoreId(data[0].id)
        }

        // Focus the select after stores are loaded
        setTimeout(() => selectRef.current?.focus(), 0)
      } catch (err) {
        console.error('Error fetching stores:', err)
        setError(err instanceof ApiError ? err.message : 'Failed to load stores')
      }
    }

    fetchStores()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedStoreId) {
      setError('Please select a store')
      return
    }

    setLoading(true)
    setError('')

    try {
      await runsApi.createRun({
        group_id: groupId,
        store_id: selectedStoreId
      })
      onSuccess()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create run')
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
        <h3>Create New Run</h3>
        <p className="popup-description">Select a store to start a new shopping run</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="store" className="form-label">Store</label>
            <select
              id="store"
              className="form-input"
              value={selectedStoreId}
              onChange={(e) => setSelectedStoreId(e.target.value)}
              disabled={loading || stores.length === 0}
              required
              ref={selectRef}
            >
              {stores.length === 0 && <option value="">No stores available</option>}
              {stores.map(store => (
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
                + Create New Store
              </button>
            )}
          </div>

          {stores.length > 0 && (
            <div className="form-group">
              <button
                type="button"
                onClick={() => setShowNewStorePopup(true)}
                className="btn btn-secondary btn-sm"
                disabled={loading}
              >
                + Create New Store
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
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !selectedStoreId}
              className="btn btn-success btn-md submit-button"
            >
              {loading ? 'Creating...' : 'Create Run'}
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
