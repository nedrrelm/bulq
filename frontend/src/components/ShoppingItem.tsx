import { useTranslation } from 'react-i18next'
import type { ShoppingListItem } from '../api'

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

interface ShoppingItemProps {
  item: ShoppingListItem
  onAddPrice?: (item: ShoppingListItem) => void
  onMarkPurchased?: (item: ShoppingListItem) => void
  onEditPurchase?: (item: ShoppingListItem) => void
  onUnpurchase?: (item: ShoppingListItem) => void
}

export default function ShoppingItem({
  item,
  onAddPrice,
  onMarkPurchased,
  onEditPurchase,
  onUnpurchase
}: ShoppingItemProps) {
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
          {(onEditPurchase || onUnpurchase) && (
            <div className="item-actions">
              {onEditPurchase && (
                <button onClick={() => onEditPurchase(item)} className="btn btn-secondary btn-sm">
                  {t('shopping:actions.editPurchase')}
                </button>
              )}
              {onUnpurchase && (
                <button onClick={() => onUnpurchase(item)} className="btn btn-ghost btn-sm">
                  {t('shopping:actions.unpurchase')}
                </button>
              )}
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
