import { useState, useEffect } from 'react'
import './ShoppingPage.css'
import { API_BASE_URL } from '../config'

interface EncounteredPrice {
  price: number
  notes: string
}

interface ShoppingListItem {
  id: string
  product_id: string
  product_name: string
  requested_quantity: number
  encountered_prices: EncounteredPrice[]
  purchased_quantity: number | null
  purchased_price_per_unit: string | null
  purchased_total: string | null
  is_purchased: boolean
  purchase_order: number | null
}

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

  const fetchShoppingList = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await fetch(`${API_BASE_URL}/shopping/${runId}/items`, {
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Failed to load shopping list')
      }

      const data: ShoppingListItem[] = await response.json()
      setItems(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load shopping list')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchShoppingList()
  }, [runId])

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
      const response = await fetch(
        `${API_BASE_URL}/shopping/${runId}/items/${selectedItem.id}/encountered-price`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ price, notes })
        }
      )

      if (!response.ok) throw new Error('Failed to add price')

      await fetchShoppingList()
      setShowPricePopup(false)
      setSelectedItem(null)
    } catch (err) {
      console.error('Error adding price:', err)
      alert('Failed to add price. Please try again.')
    }
  }

  const handleSubmitPurchase = async (quantity: number, pricePerUnit: number, total: number) => {
    if (!selectedItem) return

    try {
      const response = await fetch(
        `${API_BASE_URL}/shopping/${runId}/items/${selectedItem.id}/purchase`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            quantity,
            price_per_unit: pricePerUnit,
            total
          })
        }
      )

      if (!response.ok) throw new Error('Failed to mark as purchased')

      await fetchShoppingList()
      setShowPurchasePopup(false)
      setSelectedItem(null)
    } catch (err) {
      console.error('Error marking purchased:', err)
      alert('Failed to mark as purchased. Please try again.')
    }
  }

  const handleCompleteShopping = async () => {
    if (unpurchasedItems.length > 0) {
      const confirm = window.confirm(
        `You still have ${unpurchasedItems.length} items not purchased. Are you sure you want to complete shopping?`
      )
      if (!confirm) return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/shopping/${runId}/complete`, {
        method: 'POST',
        credentials: 'include'
      })

      if (!response.ok) throw new Error('Failed to complete shopping')

      // Navigate back to run page
      onBack()
    } catch (err) {
      console.error('Error completing shopping:', err)
      alert('Failed to complete shopping. Please try again.')
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const priceNum = parseFloat(price)
    if (isNaN(priceNum) || priceNum <= 0) {
      alert('Please enter a valid price')
      return
    }
    onSubmit(priceNum, notes)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-sm" onClick={e => e.stopPropagation()}>
        <h3>Add Encountered Price</h3>
        <p><strong>{item.product_name}</strong></p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Price ($)</label>
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={e => setPrice(e.target.value)}
              placeholder="24.99"
              className="form-input"
              autoFocus
              required
            />
          </div>
          <div className="form-group">
            <label>Notes (optional)</label>
            <input
              type="text"
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="e.g., aisle 3, vendor A"
              className="form-input"
            />
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

  const handleQuantityChange = (newQuantity: string) => {
    setQuantity(newQuantity)
    if (priceMode === 'unit' && pricePerUnit) {
      const calc = parseFloat(newQuantity) * parseFloat(pricePerUnit)
      setTotal(calc.toFixed(2))
    } else if (priceMode === 'total' && total) {
      const calc = parseFloat(total) / parseFloat(newQuantity)
      setPricePerUnit(calc.toFixed(2))
    }
  }

  const handlePricePerUnitChange = (newPrice: string) => {
    setPricePerUnit(newPrice)
    setPriceMode('unit')
    if (quantity && newPrice) {
      const calc = parseFloat(quantity) * parseFloat(newPrice)
      setTotal(calc.toFixed(2))
    }
  }

  const handleTotalChange = (newTotal: string) => {
    setTotal(newTotal)
    setPriceMode('total')
    if (quantity && newTotal) {
      const calc = parseFloat(newTotal) / parseFloat(quantity)
      setPricePerUnit(calc.toFixed(2))
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const qtyNum = parseInt(quantity)
    const priceNum = parseFloat(pricePerUnit)
    const totalNum = parseFloat(total)

    if (isNaN(qtyNum) || qtyNum <= 0) {
      alert('Please enter a valid quantity')
      return
    }
    if (isNaN(priceNum) || priceNum <= 0) {
      alert('Please enter a valid price')
      return
    }
    if (isNaN(totalNum) || totalNum <= 0) {
      alert('Please enter a valid total')
      return
    }

    onSubmit(qtyNum, priceNum, totalNum)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-sm" onClick={e => e.stopPropagation()}>
        <h3>Mark as Purchased</h3>
        <p><strong>{item.product_name}</strong></p>
        <p className="requested-hint">Requested: {item.requested_quantity}</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Quantity Purchased</label>
            <input
              type="number"
              value={quantity}
              onChange={e => handleQuantityChange(e.target.value)}
              className="form-input"
              autoFocus
              required
            />
          </div>
          <div className="form-group">
            <label>Price per Unit ($)</label>
            <input
              type="number"
              step="0.01"
              value={pricePerUnit}
              onChange={e => handlePricePerUnitChange(e.target.value)}
              placeholder="12.99"
              className="form-input"
              required
            />
          </div>
          <div className="form-group">
            <label>Total Price ($)</label>
            <input
              type="number"
              step="0.01"
              value={total}
              onChange={e => handleTotalChange(e.target.value)}
              placeholder="25.98"
              className="form-input"
              required
            />
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
