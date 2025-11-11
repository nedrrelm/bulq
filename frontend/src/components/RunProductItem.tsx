import { memo } from 'react'
import type { RunDetail } from '../api'

type Product = RunDetail['products'][0]

interface RunProductItemProps {
  product: Product
  runState: string
  canBid: boolean
  onPlaceBid: (product: Product) => void
  onRetractBid: (product: Product) => void
  getUserInitials: (name: string, allNames?: string[]) => string
}

/**
 * RunProductItem - Displays a product with bidding information in a run
 *
 * This component handles the display logic for products in different run states:
 * - Planning/Active: Show bids, allow bidding
 * - Adjusting: Show purchase quantities and adjustment status
 * - Distributing/Completed: Show final purchase information
 */
const RunProductItem = memo(({ product, runState, canBid, onPlaceBid, onRetractBid, getUserInitials }: RunProductItemProps) => {
  const needsAdjustment = runState === 'adjusting' &&
                          product.purchased_quantity !== null &&
                          product.purchased_quantity > 0 &&
                          product.total_quantity > product.purchased_quantity
  const adjustmentOk = runState === 'adjusting' &&
                       product.purchased_quantity !== null &&
                       product.purchased_quantity > 0 &&
                       product.total_quantity === product.purchased_quantity
  const notPurchasedAdjusting = runState === 'adjusting' &&
                                (product.purchased_quantity === null || product.purchased_quantity === 0)

  // Post-shopping status indicators for distributing/completed states
  const isPostShopping = runState === 'distributing' || runState === 'completed'
  const fullyPurchased = isPostShopping &&
                         product.purchased_quantity !== null &&
                         product.purchased_quantity > 0 &&
                         product.purchased_quantity === product.total_quantity
  const partiallyPurchased = isPostShopping &&
                             product.purchased_quantity !== null &&
                             product.purchased_quantity > 0 &&
                             product.purchased_quantity < product.total_quantity
  const notPurchasedFinal = isPostShopping &&
                            (product.purchased_quantity === null || product.purchased_quantity === 0)

  const shortage = product.purchased_quantity !== null ? product.total_quantity - product.purchased_quantity : 0
  const canRetract = !adjustmentOk && !(runState === 'adjusting' && product.current_user_bid && !product.current_user_bid.interested_only && product.current_user_bid.quantity > shortage)

  return (
    <div className={`product-item ${needsAdjustment ? 'needs-adjustment' : adjustmentOk ? 'adjustment-ok' : notPurchasedAdjusting ? 'not-purchased-adjusting' : ''} ${fullyPurchased ? 'adjustment-ok' : partiallyPurchased ? 'needs-adjustment' : notPurchasedFinal ? 'not-purchased-adjusting' : ''}`}>
      <div className="product-header">
        <h4>{product.name}</h4>
        {product.current_price && <span className="product-price">{product.current_price} RSD</span>}
      </div>

      {runState === 'adjusting' && (
        <div>
          {product.purchased_quantity !== null && product.purchased_quantity > 0 ? (
            <div className={`adjustment-info ${needsAdjustment ? 'needs-adjustment' : 'adjustment-ok'}`}>
              <strong>Purchased:</strong> {product.purchased_quantity}{product.unit ? ` ${product.unit}` : ''} | <strong>Requested:</strong> {product.total_quantity}{product.unit ? ` ${product.unit}` : ''}
              {needsAdjustment && (
                <span className="adjustment-warning">
                  ⚠ Reduce by {product.total_quantity - product.purchased_quantity}{product.unit ? ` ${product.unit}` : ''}
                </span>
              )}
              {adjustmentOk && (
                <span className="adjustment-ok-badge">
                  ✓ OK
                </span>
              )}
            </div>
          ) : (
            <div className="adjustment-info not-purchased-info">
              <strong>Not Purchased</strong>
              <span className="not-purchased-badge">
                ❌ Not Purchased
              </span>
            </div>
          )}
        </div>
      )}

      {isPostShopping && (
        <div>
          {(fullyPurchased || partiallyPurchased) && (
            <div className={`adjustment-info ${fullyPurchased ? 'adjustment-ok' : 'needs-adjustment'}`}>
              <strong>Purchased:</strong> {product.purchased_quantity}{product.unit ? ` ${product.unit}` : ''} | <strong>Requested:</strong> {product.total_quantity}{product.unit ? ` ${product.unit}` : ''}
              {fullyPurchased && (
                <span className="adjustment-ok-badge">
                  ✓ OK
                </span>
              )}
              {partiallyPurchased && (
                <span className="adjustment-warning">
                  ⚠️ Partially Purchased
                </span>
              )}
            </div>
          )}
          {notPurchasedFinal && (
            <div className="adjustment-info not-purchased-info">
              <strong>Not Purchased</strong>
              <span className="not-purchased-badge">
                ❌ Not Purchased
              </span>
            </div>
          )}
        </div>
      )}

      <div className="product-stats">
        <div className="stat">
          <span className="stat-value">{product.total_quantity}{product.unit ? ` ${product.unit}` : ''}</span>
          <span className="stat-label">Total Quantity</span>
        </div>
        <div className="stat">
          <span className="stat-value">{product.interested_count}</span>
          <span className="stat-label">People Interested</span>
        </div>
      </div>

      <div className="bid-users">
        <h5>Bidders:</h5>
        <div className="user-avatars">
          {product.user_bids.map((bid, index) => {
            const allBidderNames = product.user_bids.map(b => b.user_name)
            return (
            <div key={`${bid.user_id}-${index}`} className="user-avatar" title={`${bid.user_name}: ${bid.interested_only ? 'Interested' : `${bid.quantity}${product.unit ? ` ${product.unit}` : ''}`}`}>
              <span className="avatar-initials">{getUserInitials(bid.user_name, allBidderNames)}</span>
              <span className="bid-quantity">
                {bid.interested_only ? '?' : bid.quantity}
              </span>
            </div>
            )
          })}
        </div>
      </div>

      {canBid && (
        <div className="bid-actions">
          {runState === 'adjusting' ? (
            // Adjustment state button rules
            <>
              {needsAdjustment && product.current_user_bid ? (
                <div className="user-bid-status">
                  <span className="current-bid">
                    Your bid: {product.current_user_bid.interested_only ? 'Interested' : `${product.current_user_bid.quantity}${product.unit ? ` ${product.unit}` : ''}`}
                  </span>
                  <div className="bid-buttons">
                    <button
                      onClick={() => onPlaceBid(product)}
                      className="edit-bid-button"
                      title="Edit bid"
                    >
                      ✏️
                    </button>
                    {canRetract && (
                      <button
                        onClick={() => onRetractBid(product)}
                        className="retract-bid-button"
                        title="Retract bid"
                      >
                        −
                      </button>
                    )}
                  </div>
                </div>
              ) : product.current_user_bid && (adjustmentOk || notPurchasedAdjusting) ? (
                <div className="user-bid-status">
                  <span className="current-bid">
                    Your bid: {product.current_user_bid.interested_only ? 'Interested' : `${product.current_user_bid.quantity}${product.unit ? ` ${product.unit}` : ''}`}
                  </span>
                </div>
              ) : null}
            </>
          ) : (
            // Non-adjustment states (active, etc.)
            <>
              {product.current_user_bid ? (
                <div className="user-bid-status">
                  <span className="current-bid">
                    Your bid: {product.current_user_bid.interested_only ? 'Interested' : `${product.current_user_bid.quantity}${product.unit ? ` ${product.unit}` : ''}`}
                  </span>
                  <div className="bid-buttons">
                    <button
                      onClick={() => onPlaceBid(product)}
                      className="edit-bid-button"
                      title="Edit bid"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => onRetractBid(product)}
                      className="retract-bid-button"
                      title="Retract bid"
                    >
                      −
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => onPlaceBid(product)}
                  className="place-bid-button"
                  title="Place bid"
                >
                  +
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}, (prevProps, nextProps) => {
  // Only re-render if relevant props changed
  return (
    prevProps.product.id === nextProps.product.id &&
    prevProps.product.total_quantity === nextProps.product.total_quantity &&
    prevProps.product.interested_count === nextProps.product.interested_count &&
    prevProps.product.user_bids.length === nextProps.product.user_bids.length &&
    prevProps.product.current_user_bid?.quantity === nextProps.product.current_user_bid?.quantity &&
    prevProps.product.current_user_bid?.interested_only === nextProps.product.current_user_bid?.interested_only &&
    prevProps.product.purchased_quantity === nextProps.product.purchased_quantity &&
    prevProps.runState === nextProps.runState &&
    prevProps.canBid === nextProps.canBid
  )
})

RunProductItem.displayName = 'RunProductItem'

export default RunProductItem
