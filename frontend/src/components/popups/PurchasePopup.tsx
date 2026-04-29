import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import type { ShoppingListItem } from '../../api'
import { useModalFocusTrap } from '../../hooks/useModalFocusTrap'
import { validateDecimal, parseDecimal } from '../../utils/validation'

interface PurchasePopupProps {
  item: ShoppingListItem
  isEditMode?: boolean
  onSubmit: (quantity: number, pricePerUnit: number, total: number) => void
  onClose: () => void
}

export default function PurchasePopup({
  item,
  isEditMode = false,
  onSubmit,
  onClose
}: PurchasePopupProps) {
  const { t } = useTranslation(['common', 'shopping'])
  const [quantity, setQuantity] = useState(
    isEditMode && item.purchased_quantity
      ? item.purchased_quantity.toString()
      : item.requested_quantity.toString()
  )
  const [pricePerUnit, setPricePerUnit] = useState(
    isEditMode && item.purchased_price_per_unit
      ? item.purchased_price_per_unit
      : ''
  )
  const [total, setTotal] = useState(
    isEditMode && item.purchased_total
      ? item.purchased_total
      : ''
  )
  const [priceMode, setPriceMode] = useState<'unit' | 'total'>('unit')
  const [quantityError, setQuantityError] = useState('')
  const [priceError, setPriceError] = useState('')
  const [totalError, setTotalError] = useState('')
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef)

  const validateQuantity = (value: string): boolean => {
    setQuantityError('')

    const validation = validateDecimal(value, 0.01, 9999, 2, 'Quantity')
    if (!validation.isValid) {
      setQuantityError(validation.error || t('shopping:errors.invalidQuantity'))
      return false
    }

    const qty = parseDecimal(value)
    if (qty === 0) {
      setQuantityError(t('shopping:errors.quantityGreaterThanZero'))
      return false
    }

    return true
  }

  const validatePrice = (value: string): boolean => {
    setPriceError('')

    const validation = validateDecimal(value, 0.01, 99999.99, 2, 'Price per unit')
    if (!validation.isValid) {
      setPriceError(validation.error || t('shopping:errors.invalidPrice'))
      return false
    }

    return true
  }

  const validateTotal = (value: string): boolean => {
    setTotalError('')

    const validation = validateDecimal(value, 0.01, 999999.99, 2, 'Total')
    if (!validation.isValid) {
      setTotalError(validation.error || t('shopping:errors.invalidTotal'))
      return false
    }

    return true
  }

  const handleQuantityChange = (newQuantity: string) => {
    setQuantity(newQuantity)
    setQuantityError('')
    if (priceMode === 'unit' && pricePerUnit) {
      const qtyNum = parseFloat(newQuantity)
      const priceNum = parseFloat(pricePerUnit)
      if (!isNaN(qtyNum) && !isNaN(priceNum)) {
        setTotal((qtyNum * priceNum).toFixed(2))
      }
    } else if (priceMode === 'total' && total) {
      const qtyNum = parseFloat(newQuantity)
      const totalNum = parseFloat(total)
      if (!isNaN(qtyNum) && !isNaN(totalNum) && qtyNum !== 0) {
        setPricePerUnit((totalNum / qtyNum).toFixed(2))
      }
    }
  }

  const handlePricePerUnitChange = (newPrice: string) => {
    setPricePerUnit(newPrice)
    setPriceError('')
    setPriceMode('unit')
    if (quantity && newPrice) {
      const qtyNum = parseFloat(quantity)
      const priceNum = parseFloat(newPrice)
      if (!isNaN(qtyNum) && !isNaN(priceNum)) {
        setTotal((qtyNum * priceNum).toFixed(2))
      }
    }
  }

  const handleTotalChange = (newTotal: string) => {
    setTotal(newTotal)
    setTotalError('')
    setPriceMode('total')
    if (quantity && newTotal) {
      const qtyNum = parseFloat(quantity)
      const totalNum = parseFloat(newTotal)
      if (!isNaN(qtyNum) && !isNaN(totalNum) && qtyNum !== 0) {
        setPricePerUnit((totalNum / qtyNum).toFixed(2))
      }
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const isQuantityValid = validateQuantity(quantity)
    const isPriceValid = validatePrice(pricePerUnit)
    const isTotalValid = validateTotal(total)

    if (!isQuantityValid || !isPriceValid || !isTotalValid) {
      return
    }

    const qtyNum = parseDecimal(quantity)
    const priceNum = parseDecimal(pricePerUnit)
    const totalNum = parseDecimal(total)

    onSubmit(qtyNum, priceNum, totalNum)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal modal-sm" onClick={e => e.stopPropagation()}>
        <h3>{isEditMode ? t('shopping:actions.editPurchase') : t('shopping:actions.markPurchased')}</h3>
        <p><strong>{item.product_name}</strong></p>
        <p className="requested-hint">
          {isEditMode
            ? `${t('shopping:labels.currentPurchase')}: ${item.purchased_quantity}${item.product_unit ? ` ${item.product_unit}` : ''}`
            : `${t('shopping:labels.requested')}: ${item.requested_quantity}${item.product_unit ? ` ${item.product_unit}` : ''}`
          }
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t('shopping:fields.quantityPurchased')}</label>
            <input
              type="number"
              step="0.01"
              value={quantity}
              onChange={e => handleQuantityChange(e.target.value)}
              className={`form-input ${quantityError ? 'input-error' : ''}`}
              autoFocus
              required
              min="0.01"
            />
            {quantityError && <span className="error-message">{quantityError}</span>}
          </div>
          <div className="form-group">
            <label>{t('shopping:fields.pricePerUnit')}</label>
            <input
              type="number"
              step="0.01"
              value={pricePerUnit}
              onChange={e => handlePricePerUnitChange(e.target.value)}
              placeholder="12.99"
              className={`form-input ${priceError ? 'input-error' : ''}`}
              required
              min="0.01"
            />
            {priceError && <span className="error-message">{priceError}</span>}
          </div>
          <div className="form-group">
            <label>{t('shopping:fields.totalPrice')}</label>
            <input
              type="number"
              step="0.01"
              value={total}
              onChange={e => handleTotalChange(e.target.value)}
              placeholder="25.98"
              className={`form-input ${totalError ? 'input-error' : ''}`}
              required
              min="0.01"
            />
            {totalError && <span className="error-message">{totalError}</span>}
          </div>
          <div className="button-group">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              {t('common:actions.cancel')}
            </button>
            <button type="submit" className="btn btn-success">
              {isEditMode ? t('shopping:actions.updatePurchase') : t('shopping:actions.confirmPurchase')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
