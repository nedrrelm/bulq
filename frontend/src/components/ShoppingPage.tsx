import { useState, useRef, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import '../styles/components/ShoppingPage.css'
import { WS_BASE_URL } from '../config'
import { shoppingApi } from '../api'
import type { ShoppingListItem } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { useWebSocket } from '../hooks/useWebSocket'
import Toast from './Toast'
import ConfirmDialog from './ConfirmDialog'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { validateDecimal, parseDecimal, sanitizeString } from '../utils/validation'
import { useShoppingList, shoppingKeys } from '../hooks/queries'
import { formatErrorForDisplay, getErrorMessage } from '../utils/errorHandling'
import { MAX_NOTES_LENGTH } from '../constants'

// Using ShoppingListItem type from API layer

// Helper function to format price observation date
function formatPriceDate(dateStr: string | null, t: (key: string) => string): string {
  if (!dateStr) return t('shopping:labels.unknownDate')

  const date = new Date(dateStr)
  const today = new Date()
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  // Reset time portions for comparison
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const yesterdayOnly = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate())

  if (dateOnly.getTime() === todayOnly.getTime()) {
    return t('shopping:labels.today')
  } else if (dateOnly.getTime() === yesterdayOnly.getTime()) {
    return t('shopping:labels.yesterday')
  } else {
    // Format as "on Mar 15" or "on Mar 15, 2024" if different year
    const options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' }
    if (date.getFullYear() !== today.getFullYear()) {
      options.year = 'numeric'
    }
    return t('shopping:labels.on') + ' ' + date.toLocaleDateString('en-US', options)
  }
}

export default function ShoppingPage() {
  const { t } = useTranslation(['common', 'shopping'])
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()

  // Redirect if no runId
  if (!runId) {
    navigate('/')
    return null
  }

  const { data: items = [], isLoading: loading, error: queryError } = useShoppingList(runId)
  const queryClient = useQueryClient()

  const error = getErrorMessage(queryError, '')

  const [showPurchasePopup, setShowPurchasePopup] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ShoppingListItem | null>(null)
  const [showPricePopup, setShowPricePopup] = useState(false)
  const [showBuyMorePopup, setShowBuyMorePopup] = useState(false)
  const { toast, showToast, hideToast} = useToast()
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

  // WebSocket for real-time updates
  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'shopping_item_updated') {
      // Invalidate shopping list to refetch with updates
      queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
    }
  }, [queryClient, runId])

  useWebSocket(
    runId ? `${WS_BASE_URL}/ws/runs/${runId}` : null,
    {
      onMessage: handleWebSocketMessage
    }
  )

  const handleAddPrice = (item: ShoppingListItem) => {
    setSelectedItem(item)
    setShowPricePopup(true)
  }

  const handleMarkPurchased = (item: ShoppingListItem) => {
    setSelectedItem(item)
    setShowPurchasePopup(true)
  }

  const handleBuyMore = (item: ShoppingListItem) => {
    setSelectedItem(item)
    setShowBuyMorePopup(true)
  }

  const handleSubmitPrice = async (price: number, notes: string, minimumQuantity?: number) => {
    if (!selectedItem) return

    try {
      await shoppingApi.updateAvailabilityPrice(runId, selectedItem.id, {
        price,
        notes,
        minimum_quantity: minimumQuantity
      })
      // Invalidate shopping list to refetch with updates
      queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
      setShowPricePopup(false)
      setSelectedItem(null)
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'add price'), 'error')
    }
  }

  const handleSubmitPurchase = async (quantity: number, pricePerUnit: number, total: number) => {
    if (!selectedItem) return

    try {
      await shoppingApi.markPurchased(runId, selectedItem.id, {
        quantity,
        price_per_unit: pricePerUnit,
        total
      })
      // Invalidate shopping list to refetch with updates
      queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
      setShowPurchasePopup(false)
      setSelectedItem(null)
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'mark as purchased'), 'error')
    }
  }

  const handleSubmitBuyMore = async (quantity: number, pricePerUnit: number, total: number) => {
    if (!selectedItem) return

    try {
      await shoppingApi.addMorePurchase(runId, selectedItem.id, {
        quantity,
        price_per_unit: pricePerUnit,
        total
      })
      // Invalidate shopping list to refetch with updates
      queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
      setShowBuyMorePopup(false)
      setSelectedItem(null)
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'add more purchase'), 'error')
    }
  }

  const handleCompleteShopping = async () => {
    const completeShoppingAction = async () => {
      try {
        await shoppingApi.completeShopping(runId)
        // Navigate back to run page
        navigate(`/runs/${runId}`)
      } catch (err) {
        showToast(formatErrorForDisplay(err, 'complete shopping'), 'error')
      }
    }

    if (unpurchasedItems.length > 0) {
      showConfirm(
        t('shopping:prompts.unpurchasedItems', { count: unpurchasedItems.length }),
        completeShoppingAction
      )
    } else {
      completeShoppingAction()
    }
  }

  const unpurchasedItems = items.filter(item => !item.is_purchased)
  const purchasedItems = items.filter(item => item.is_purchased)
  const totalSpent = purchasedItems.reduce((sum, item) => {
    return sum + (parseFloat(item.purchased_total || '0'))
  }, 0)

  if (loading) {
    return (
      <div className="shopping-page">
        <button onClick={() => navigate(`/runs/${runId}`)} className="back-button">{t('shopping:navigation.backToRun')}</button>
        <p>{t('shopping:messages.loadingShoppingList')}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="shopping-page">
        <button onClick={() => navigate(`/runs/${runId}`)} className="back-button">{t('shopping:navigation.backToRun')}</button>
        <div className="error">
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="shopping-page">
      <div className="shopping-header">
        <button onClick={() => navigate(`/runs/${runId}`)} className="back-button">{t('shopping:navigation.backToRun')}</button>
        <h2>{t('shopping:labels.shoppingMode')}</h2>
        <div className="header-actions">
          <div className="total-display">
            {t('shopping:labels.total')}: {totalSpent.toFixed(2)} RSD
          </div>
          <button onClick={handleCompleteShopping} className="btn btn-success btn-lg">
            {t('shopping:actions.completeShopping')}
          </button>
        </div>
      </div>

      <div className="shopping-content">
        {unpurchasedItems.length > 0 && (
          <div className="shopping-section">
            <h3>{t('shopping:labels.toBuy', { count: unpurchasedItems.length })}</h3>
            <div className="shopping-list">
              {unpurchasedItems.map(item => (
                <ShoppingItem
                  key={item.id}
                  item={item}
                  onAddPrice={handleAddPrice}
                  onMarkPurchased={handleMarkPurchased}
                />
              ))}
            </div>
          </div>
        )}

        {purchasedItems.length > 0 && (
          <div className="shopping-section purchased-section">
            <h3>{t('shopping:labels.purchased', { count: purchasedItems.length })}</h3>
            <div className="shopping-list">
              {purchasedItems.map(item => (
                <ShoppingItem key={item.id} item={item} onBuyMore={handleBuyMore} />
              ))}
            </div>
          </div>
        )}
      </div>

      {showPricePopup && selectedItem && (
        <PricePopup
          item={selectedItem}
          onSubmit={handleSubmitPrice}
          onClose={() => {
            setShowPricePopup(false)
            setSelectedItem(null)
          }}
        />
      )}

      {showPurchasePopup && selectedItem && (
        <PurchasePopup
          item={selectedItem}
          onSubmit={handleSubmitPurchase}
          onClose={() => {
            setShowPurchasePopup(false)
            setSelectedItem(null)
          }}
        />
      )}

      {showBuyMorePopup && selectedItem && (
        <BuyMorePopup
          item={selectedItem}
          onSubmit={handleSubmitBuyMore}
          onClose={() => {
            setShowBuyMorePopup(false)
            setSelectedItem(null)
          }}
        />
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
        />
      )}

      {confirmState && (
        <ConfirmDialog
          message={confirmState.message}
          onConfirm={handleConfirm}
          onCancel={hideConfirm}
        />
      )}
    </div>
  )
}

function ShoppingItem({
  item,
  onAddPrice,
  onMarkPurchased,
  onBuyMore
}: {
  item: ShoppingListItem
  onAddPrice?: (item: ShoppingListItem) => void
  onMarkPurchased?: (item: ShoppingListItem) => void
  onBuyMore?: (item: ShoppingListItem) => void
}) {
  const { t } = useTranslation(['common', 'shopping'])
  const isPurchased = item.is_purchased
  const quantityDiffers = isPurchased && item.purchased_quantity !== item.requested_quantity

  return (
    <div className={`shopping-item ${isPurchased ? 'purchased' : ''}`}>
      <div className="item-header">
        <h4>{item.product_name}</h4>
        <div className="quantity-display">
          {isPurchased ? (
            <>
              <span className={quantityDiffers ? 'quantity-differs' : ''}>
                {item.purchased_quantity}{item.product_unit ? ` ${item.product_unit}` : ''} {quantityDiffers && `/ ${item.requested_quantity}${item.product_unit ? ` ${item.product_unit}` : ''}`}
              </span>
            </>
          ) : (
            <span>{item.requested_quantity}{item.product_unit ? ` ${item.product_unit}` : ''}</span>
          )}
        </div>
      </div>

      {item.recent_prices.length > 0 && item.recent_prices[0] && (
        <div className="availability-info">
          <small>
            {t('shopping:labels.pricesSeen')} {formatPriceDate(item.recent_prices[0].created_at, t)}:
          </small>
          {item.recent_prices.map((priceObs, idx) => (
            <div key={idx} className="price-tag">
              {priceObs.price.toFixed(2)} RSD
              {priceObs.notes && <span className="price-notes"> - {priceObs.notes}</span>}
            </div>
          ))}
        </div>
      )}

      {isPurchased ? (
        <div className="purchase-info">
          <div className="purchase-detail">
            {item.purchased_price_per_unit} RSD × {item.purchased_quantity}{item.product_unit ? ` ${item.product_unit}` : ''} = <strong>{item.purchased_total} RSD</strong>
          </div>
          {onBuyMore && (
            <div className="item-actions">
              <button onClick={() => onBuyMore(item)} className="btn btn-primary btn-sm">
                {t('shopping:actions.buyMore')}
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="item-actions">
          {onAddPrice && (
            <button onClick={() => onAddPrice(item)} className="btn btn-secondary btn-sm">
              {t('shopping:actions.addPrice')}
            </button>
          )}
          {onMarkPurchased && (
            <button onClick={() => onMarkPurchased(item)} className="btn btn-success btn-sm">
              {t('shopping:actions.markPurchased')}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// MAX_NOTES_LENGTH imported from constants

function PricePopup({
  item,
  onSubmit,
  onClose
}: {
  item: ShoppingListItem
  onSubmit: (price: number, notes: string, minimumQuantity?: number) => void
  onClose: () => void
}) {
  const { t } = useTranslation(['common', 'shopping'])
  const [price, setPrice] = useState('')
  const [notes, setNotes] = useState('')
  const [minimumQuantity, setMinimumQuantity] = useState('')
  const [priceError, setPriceError] = useState('')
  const [minQtyError, setMinQtyError] = useState('')
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

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
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal modal-sm" onClick={e => e.stopPropagation()}>
        <h3>{t('shopping:actions.updatePrice')}</h3>
        <p><strong>{item.product_name}</strong></p>
        <form onSubmit={handleSubmit}>
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
          <div className="button-group">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              {t('common:actions.cancel')}
            </button>
            <button type="submit" className="btn btn-primary">
              {t('shopping:actions.addPrice')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function BuyMorePopup({
  item,
  onSubmit,
  onClose
}: {
  item: ShoppingListItem
  onSubmit: (quantity: number, pricePerUnit: number, total: number) => void
  onClose: () => void
}) {
  const { t } = useTranslation(['common', 'shopping'])
  const [quantity, setQuantity] = useState('')
  const [pricePerUnit, setPricePerUnit] = useState('')
  const [total, setTotal] = useState('')
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
        <h3>{t('shopping:actions.buyMore')}</h3>
        <p><strong>{item.product_name}</strong></p>
        <p className="requested-hint">
          {t('shopping:labels.alreadyPurchased')}: {item.purchased_quantity}{item.product_unit ? ` ${item.product_unit}` : ''}
        </p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>{t('shopping:fields.additionalQuantity')}</label>
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
            <button type="submit" className="btn btn-primary">
              {t('shopping:actions.addPurchase')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

function PurchasePopup({
  item,
  onSubmit,
  onClose
}: {
  item: ShoppingListItem
  onSubmit: (quantity: number, pricePerUnit: number, total: number) => void
  onClose: () => void
}) {
  const { t } = useTranslation(['common', 'shopping'])
  const [quantity, setQuantity] = useState(item.requested_quantity.toString())
  const [pricePerUnit, setPricePerUnit] = useState('')
  const [total, setTotal] = useState('')
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
        <h3>{t('shopping:actions.markPurchased')}</h3>
        <p><strong>{item.product_name}</strong></p>
        <p className="requested-hint">{t('shopping:labels.requested')}: {item.requested_quantity}{item.product_unit ? ` ${item.product_unit}` : ''}</p>
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
              {t('shopping:actions.confirmPurchase')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
