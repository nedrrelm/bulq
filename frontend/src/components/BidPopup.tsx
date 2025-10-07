import { useState, useRef, useEffect } from 'react'
import './BidPopup.css'

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
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    // Autofocus the input when component mounts
    if (inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const qty = parseInt(quantity) || 0

    // Validation
    if (qty < 0) return
    if (adjustingMode && minAllowed !== undefined && qty < minAllowed) {
      alert(`Minimum allowed quantity is ${minAllowed}`)
      return
    }
    if (adjustingMode && maxAllowed !== undefined && qty > maxAllowed) {
      alert(`Maximum allowed quantity is ${maxAllowed}`)
      return
    }

    onSubmit(qty, interestedOnly)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel()
    }
  }

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal modal-sm" onClick={(e) => e.stopPropagation()} onKeyDown={handleKeyDown}>
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
              min={adjustingMode && minAllowed !== undefined ? minAllowed : 0}
              max={adjustingMode && maxAllowed !== undefined ? maxAllowed : undefined}
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="quantity-input"
            />
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