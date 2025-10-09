import { useState, useRef, useEffect } from 'react'
import './BidPopup.css'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { validateDecimal, parseDecimal } from '../utils/validation'

interface BidPopupProps {
  productName: string
  currentQuantity?: number
  onSubmit: (quantity: number, interestedOnly: boolean) => void
  onCancel: () => void
  adjustingMode?: boolean
  minAllowed?: number
  maxAllowed?: number
}

export default function BidPopup({ productName, currentQuantity, onSubmit, onCancel, adjustingMode, minAllowed, maxAllowed }: BidPopupProps) {
  const [quantity, setQuantity] = useState(currentQuantity?.toString() || '1')
  const [interestedOnly, setInterestedOnly] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onCancel)

  useEffect(() => {
    // Autofocus the input when component mounts
    if (inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [])

  const validateQuantity = (value: string): boolean => {
    setError('')

    if (interestedOnly) {
      return true // No quantity validation for "interested only"
    }

    const min = adjustingMode && minAllowed !== undefined ? minAllowed : 0
    const max = adjustingMode && maxAllowed !== undefined ? maxAllowed : 9999

    const validation = validateDecimal(value, min, max, 2, 'Quantity')

    if (!validation.isValid) {
      setError(validation.error || 'Invalid quantity')
      return false
    }

    const qty = parseDecimal(value)
    if (qty === 0) {
      setError('Quantity must be greater than 0')
      return false
    }

    return true
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateQuantity(quantity)) {
      return
    }

    const qty = parseDecimal(quantity)
    onSubmit(qty, interestedOnly)
  }

  const handleQuantityChange = (value: string) => {
    setQuantity(value)
    setError('') // Clear error on change
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel()
    }
  }

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div ref={modalRef} className="modal modal-sm" onClick={(e) => e.stopPropagation()} onKeyDown={handleKeyDown}>
        <h3>{adjustingMode ? 'Adjust Bid' : 'Place Bid'}</h3>
        <p className="product-name">{productName}</p>

        {adjustingMode && (
          <div className="adjusting-mode-notice">
            <strong>⚠️ Adjusting Mode</strong>
            <p>
              You can only reduce your bid.
              {minAllowed !== undefined && maxAllowed !== undefined && (
                <> Range: {minAllowed} - {maxAllowed} items</>
              )}
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="quantity">Quantity:</label>
            <input
              ref={inputRef}
              id="quantity"
              type="number"
              step="0.01"
              min={adjustingMode && minAllowed !== undefined ? minAllowed : 0}
              max={adjustingMode && maxAllowed !== undefined ? maxAllowed : undefined}
              value={quantity}
              onChange={(e) => handleQuantityChange(e.target.value)}
              className={`quantity-input ${error ? 'input-error' : ''}`}
              disabled={interestedOnly}
            />
            {error && <span className="error-message">{error}</span>}
            <small className="input-hint">You can enter decimals (e.g., 0.5, 1.25)</small>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={interestedOnly}
                onChange={(e) => setInterestedOnly(e.target.checked)}
              />
              Interested only (no quantity commitment)
            </label>
          </div>

          <div className="button-group">
            <button type="button" onClick={onCancel} className="cancel-button">
              Cancel
            </button>
            <button type="submit" className="submit-button">
              {currentQuantity !== undefined ? 'Update Bid' : 'Place Bid'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}