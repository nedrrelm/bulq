import { useState, useEffect, useRef } from 'react'
import './NewRunPopup.css'
import { API_BASE_URL } from '../config'
import type { Store } from '../types/store'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'

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
  const overlayRef = useRef<HTMLDivElement>(null)
  const selectRef = useRef<HTMLSelectElement>(null)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef)

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)

    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  useEffect(() => {
    const fetchStores = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/stores`, {
          credentials: 'include'
        })

        if (!response.ok) {
          const errorText = await response.text()
          throw new Error(`Failed to fetch stores: ${response.status} - ${errorText}`)
        }

        const data: Store[] = await response.json()
        setStores(data)

        // Auto-select first store if available
        if (data.length > 0) {
          setSelectedStoreId(data[0].id)
        }

        // Focus the select after stores are loaded
        setTimeout(() => selectRef.current?.focus(), 0)
      } catch (err) {
        console.error('Error fetching stores:', err)
        setError(err instanceof Error ? err.message : 'Failed to load stores')
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
      const response = await fetch(`${API_BASE_URL}/runs/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          group_id: groupId,
          store_id: selectedStoreId
        })
      })

      if (!response.ok) {
        const errorData = await response.text()
        throw new Error(errorData || 'Failed to create run')
      }

      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create run')
    } finally {
      setLoading(false)
    }
  }

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose()
    }
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
          </div>

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
    </div>
  )
}
