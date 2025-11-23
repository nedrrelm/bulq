import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import '../styles/components/BidPopup.css'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { validateDecimal, parseDecimal } from '../utils/validation'

interface BidPopupProps {
  productName: string
  currentQuantity?: number
  currentComment?: string | null
  onSubmit: (quantity: number, interestedOnly: boolean, comment: string | null) => void
  onCancel: () => void
  adjustingMode?: boolean
  minAllowed?: number
  maxAllowed?: number
}

export default function BidPopup({ productName, currentQuantity, currentComment, onSubmit, onCancel, adjustingMode, minAllowed, maxAllowed }: BidPopupProps) {
  const { t } = useTranslation(['common', 'run'])
  const [quantity, setQuantity] = useState(currentQuantity?.toString() || '1')
  const [interestedOnly, setInterestedOnly] = useState(false)
  const [comment, setComment] = useState(currentComment || '')
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

    const validation = validateDecimal(value, min, max, 2, t('run:fields.quantity'))

    if (!validation.isValid) {
      setError(validation.error || t('run:validation.quantityInvalid'))
      return false
    }

    const qty = parseDecimal(value)
    if (qty === 0) {
      setError(t('run:validation.quantityGreaterThanZero'))
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
    const finalComment = comment.trim() || null
    onSubmit(qty, interestedOnly, finalComment)
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
        <h3>{adjustingMode ? t('run:bid.adjustTitle') : t('run:bid.title')}</h3>
        <p className="product-name">{productName}</p>

        {adjustingMode && (
          <div className="adjusting-mode-notice">
            <strong>{t('run:bid.adjustingModeWarning')}</strong>
            <p>
              {(() => {
                // Determine if this is a shortage (can only decrease) or surplus (can only increase)
                const isIncrease = minAllowed !== undefined && maxAllowed !== undefined &&
                                   currentQuantity !== undefined && minAllowed >= currentQuantity
                return isIncrease
                  ? t('run:bid.adjustingModeDescriptionIncrease')
                  : t('run:bid.adjustingModeDescription')
              })()}
              {minAllowed !== undefined && maxAllowed !== undefined && (
                <> {t('run:bid.range', { min: minAllowed, max: maxAllowed })}</>
              )}
            </p>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="quantity">{t('run:fields.quantity')}:</label>
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
            <small className="input-hint">{t('run:bid.decimalHint')}</small>
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={interestedOnly}
                onChange={(e) => setInterestedOnly(e.target.checked)}
              />
              {t('run:bid.interestedOnly')}
            </label>
          </div>

          <div className="form-group">
            <label htmlFor="comment">{t('run:fields.comment')}:</label>
            <textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={t('run:bid.commentPlaceholder')}
              maxLength={500}
              rows={3}
              className="comment-textarea"
            />
            <small className="input-hint">{t('run:bid.commentCounter', { count: comment.length })}</small>
          </div>

          <div className="button-group">
            <button type="button" onClick={onCancel} className="cancel-button">
              {t('common:buttons.cancel')}
            </button>
            <button type="submit" className="submit-button">
              {currentQuantity !== undefined ? t('run:actions.updateBid') : t('run:actions.placeBid')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}