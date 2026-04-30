import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { ShoppingListItem } from '../../api'
import { validateDecimal, parseDecimal, sanitizeString } from '../../utils/validation'
import { MAX_NOTES_LENGTH } from '../../constants'
import BaseModal from '../common/BaseModal'

interface PricePopupProps {
  item: ShoppingListItem
  onSubmit: (price: number, notes: string, minimumQuantity?: number) => void
  onClose: () => void
}

export default function PricePopup({ item, onSubmit, onClose }: PricePopupProps) {
  const { t } = useTranslation(['common', 'shopping'])
  const [price, setPrice] = useState('')
  const [notes, setNotes] = useState('')
  const [minimumQuantity, setMinimumQuantity] = useState('')
  const [priceError, setPriceError] = useState('')
  const [minQtyError, setMinQtyError] = useState('')

  const validatePrice = (value: string): boolean => {
    setPriceError('')

    const validation = validateDecimal(value, 0.01, 99999.99, 2, 'Price')
    if (!validation.isValid) {
      setPriceError(validation.error || t('shopping:errors.invalidPrice'))
      return false
    }

    return true
  }

  const validateMinimumQuantity = (value: string): boolean => {
    setMinQtyError('')

    if (!value) return true // Optional field

    const num = parseInt(value, 10)
    if (isNaN(num) || num < 1 || num > 9999) {
      setMinQtyError(t('shopping:errors.minimumQuantityRange'))
      return false
    }

    return true
  }

  const handlePriceChange = (value: string) => {
    setPrice(value)
    setPriceError('')
  }

  const handleNotesChange = (value: string) => {
    const sanitized = sanitizeString(value, MAX_NOTES_LENGTH)
    setNotes(sanitized)
  }

  const handleMinimumQuantityChange = (value: string) => {
    setMinimumQuantity(value)
    setMinQtyError('')
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const isPriceValid = validatePrice(price)
    const isMinQtyValid = validateMinimumQuantity(minimumQuantity)

    if (!isPriceValid || !isMinQtyValid) {
      return
    }

    const priceNum = parseDecimal(price)
    const minQty = minimumQuantity ? parseInt(minimumQuantity, 10) : undefined
    onSubmit(priceNum, notes.trim(), minQty)
  }

  const notesCharCount = notes.length

  return (
    <BaseModal
      isOpen={true}
      onClose={onClose}
      size="sm"
      submitButton={{
        text: t('shopping:actions.addPrice'),
        onClick: handleSubmit,
      }}
    >
      <h3>{t('shopping:actions.updatePrice')}</h3>
      <p><strong>{item.product_name}</strong></p>
        <div className="form-group">
          <label>{t('shopping:fields.price')}</label>
          <input
            type="number"
            step="0.01"
            value={price}
            onChange={e => handlePriceChange(e.target.value)}
            placeholder="24.99"
            className={`form-input ${priceError ? 'input-error' : ''}`}
            autoFocus
            required
            min="0.01"
          />
          {priceError && <span className="error-message">{priceError}</span>}
        </div>
        <div className="form-group">
          <label>{t('shopping:fields.minimumQuantity')}</label>
          <input
            type="number"
            value={minimumQuantity}
            onChange={e => handleMinimumQuantityChange(e.target.value)}
            placeholder={t('shopping:fields.minimumQuantityPlaceholder')}
            className={`form-input ${minQtyError ? 'input-error' : ''}`}
            min="1"
            max="9999"
          />
          {minQtyError && <span className="error-message">{minQtyError}</span>}
        </div>
        <div className="form-group">
          <label>{t('shopping:fields.notes')}</label>
          <input
            type="text"
            value={notes}
            onChange={e => handleNotesChange(e.target.value)}
            placeholder={t('shopping:fields.notesPlaceholder')}
            className="form-input"
          />
          <span className="char-counter">{notesCharCount}/{MAX_NOTES_LENGTH}</span>
        </div>
    </BaseModal>
  )
}
