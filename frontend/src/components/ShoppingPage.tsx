import { useState, useEffect, useRef } from 'react'
import './ShoppingPage.css'
import { WS_BASE_URL } from '../config'
import { shoppingApi, ApiError } from '../api'
import type { ShoppingListItem } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { useWebSocket } from '../hooks/useWebSocket'
import Toast from './Toast'
import ConfirmDialog from './ConfirmDialog'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { validateDecimal, parseDecimal, sanitizeString } from '../utils/validation'

// Using ShoppingListItem type from API layer

interface ShoppingPageProps {
  runId: string
  onBack: () => void
}

export default function ShoppingPage({ runId, onBack }: ShoppingPageProps) {
  const [items, setItems] = useState<ShoppingListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showPurchasePopup, setShowPurchasePopup] = useState(false)
  const [selectedItem, setSelectedItem] = useState<ShoppingListItem | null>(null)
  const [showPricePopup, setShowPricePopup] = useState(false)
  const { toast, showToast, hideToast } = useToast()
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

  const fetchShoppingList = async (silent = false) => {
    try {
      if (!silent) setLoading(true)
      setError('')

      const data = await shoppingApi.getShoppingList(runId)
      setItems(data)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to load shopping list')
    } finally {
      if (!silent) setLoading(false)
    }
  }

  useEffect(() => {
    fetchShoppingList()
  }, [runId])

  // WebSocket for real-time updates
  useWebSocket(
    runId ? `${WS_BASE_URL}/ws/runs/${runId}` : null,
    {
      onMessage: (message) => {
        if (message.type === 'shopping_item_updated') {
          // Refetch the shopping list to get updates (silently to avoid scroll jump)
          fetchShoppingList(true)
        }
      }
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

  const handleSubmitPrice = async (price: number, notes: string) => {
    if (!selectedItem) return

    try {
      await shoppingApi.addEncounteredPrice(runId, selectedItem.id, { price, notes })
      // Refetch shopping list to ensure UI is updated (silently to avoid scroll jump)
      await fetchShoppingList(true)
      setShowPricePopup(false)
      setSelectedItem(null)
    } catch (err) {
      console.error('Error adding price:', err)
      showToast('Failed to add price. Please try again.', 'error')
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
      // Refetch shopping list to ensure UI is updated (silently to avoid scroll jump)
      await fetchShoppingList(true)
      setShowPurchasePopup(false)
      setSelectedItem(null)
    } catch (err) {
      console.error('Error marking purchased:', err)
      showToast('Failed to mark as purchased. Please try again.', 'error')
    }
  }

  const handleCompleteShopping = async () => {
    const completeShoppingAction = async () => {
      try {
        await shoppingApi.completeShopping(runId)
        // Navigate back to run page
        onBack()
      } catch (err) {
        console.error('Error completing shopping:', err)
        showToast('Failed to complete shopping. Please try again.', 'error')
      }
    }

    if (unpurchasedItems.length > 0) {
      showConfirm(
        `You still have ${unpurchasedItems.length} items not purchased. Are you sure you want to complete shopping?`,
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
        <button onClick={onBack} className="back-button">← Back to Run</button>
        <p>Loading shopping list...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="shopping-page">
        <button onClick={onBack} className="back-button">← Back to Run</button>
        <div className="error">
          <p>❌ {error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="shopping-page">
      <div className="shopping-header">
        <button onClick={onBack} className="back-button">← Back to Run</button>
        <h2>🛒 Shopping Mode</h2>
        <div className="header-actions">
          <div className="total-display">
            Total: ${totalSpent.toFixed(2)}
          </div>
          <button onClick={handleCompleteShopping} className="btn btn-success btn-lg">
            ✓ Complete Shopping
          </button>
        </div>
      </div>

      <div className="shopping-content">
        {unpurchasedItems.length > 0 && (
          <div className="shopping-section">
            <h3>To Buy ({unpurchasedItems.length})</h3>
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
            <h3>Purchased ({purchasedItems.length})</h3>
            <div className="shopping-list">
              {purchasedItems.map(item => (
                <ShoppingItem key={item.id} item={item} />
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
  onMarkPurchased
}: {
  item: ShoppingListItem
  onAddPrice?: (item: ShoppingListItem) => void
  onMarkPurchased?: (item: ShoppingListItem) => void
}) {
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
                {item.purchased_quantity} {quantityDiffers && `/ ${item.requested_quantity}`}
              </span>
            </>
          ) : (
            <span>{item.requested_quantity}</span>
          )}
        </div>
      </div>

      {item.encountered_prices.length > 0 && (
        <div className="encountered-prices">
          <small>Prices seen:</small>
          {item.encountered_prices.map((price, idx) => (
            <div key={idx} className="price-tag">
              ${price.price.toFixed(2)}
              {price.notes && <span className="price-notes"> - {price.notes}</span>}
            </div>
          ))}
        </div>
      )}

      {isPurchased ? (
        <div className="purchase-info">
          <div className="purchase-detail">
            ${item.purchased_price_per_unit} × {item.purchased_quantity} = <strong>${item.purchased_total}</strong>
          </div>
        </div>
      ) : (
        <div className="item-actions">
          {onAddPrice && (
            <button onClick={() => onAddPrice(item)} className="btn btn-secondary btn-sm">
              💰 Add Price
            </button>
          )}
          {onMarkPurchased && (
            <button onClick={() => onMarkPurchased(item)} className="btn btn-success btn-sm">
              ✓ Mark Purchased
            </button>
          )}
        </div>
      )}
    </div>
  )
}

const MAX_NOTES_LENGTH = 200

function PricePopup({
  item,
  onSubmit,
  onClose
}: {
  item: ShoppingListItem
  onSubmit: (price: number, notes: string) => void
  onClose: () => void
}) {
  const [price, setPrice] = useState('')
  const [notes, setNotes] = useState('')
  const [priceError, setPriceError] = useState('')
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef)

  const validatePrice = (value: string): boolean => {
    setPriceError('')

    const validation = validateDecimal(value, 0.01, 99999.99, 2, 'Price')
    if (!validation.isValid) {
      setPriceError(validation.error || 'Invalid price')
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!validatePrice(price)) {
      return
    }

    const priceNum = parseDecimal(price)
    onSubmit(priceNum, notes.trim())
  }

  const notesCharCount = notes.length

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal modal-sm" onClick={e => e.stopPropagation()}>
        <h3>Add Encountered Price</h3>
        <p><strong>{item.product_name}</strong></p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Price</label>
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
            <label>Notes (optional)</label>
            <input
              type="text"
              value={notes}
              onChange={e => handleNotesChange(e.target.value)}
              placeholder="e.g., aisle 3, vendor A"
              className="form-input"
            />
            <span className="char-counter">{notesCharCount}/{MAX_NOTES_LENGTH}</span>
          </div>
          <div className="button-group">
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Add Price
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
      setQuantityError(validation.error || 'Invalid quantity')
      return false
    }

    const qty = parseDecimal(value)
    if (qty === 0) {
      setQuantityError('Quantity must be greater than 0')
      return false
    }

    return true
  }

  const validatePrice = (value: string): boolean => {
    setPriceError('')

    const validation = validateDecimal(value, 0.01, 99999.99, 2, 'Price per unit')
    if (!validation.isValid) {
      setPriceError(validation.error || 'Invalid price')
      return false
    }

    return true
  }

  const validateTotal = (value: string): boolean => {
    setTotalError('')

    const validation = validateDecimal(value, 0.01, 999999.99, 2, 'Total')
    if (!validation.isValid) {
      setTotalError(validation.error || 'Invalid total')
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
        <h3>Mark as Purchased</h3>
        <p><strong>{item.product_name}</strong></p>
        <p className="requested-hint">Requested: {item.requested_quantity}</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Quantity Purchased</label>
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
            <label>Price per Unit</label>
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
            <label>Total Price</label>
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
              Cancel
            </button>
            <button type="submit" className="btn btn-success">
              Confirm Purchase
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
