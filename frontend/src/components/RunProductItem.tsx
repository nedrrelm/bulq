import { memo } from 'react'
import { useTranslation } from 'react-i18next'
import type { RunDetail } from '../api'

type Product = RunDetail['products'][0]

interface RunProductItemProps {
  product: Product
  runState: string
  canBid: boolean
  onPlaceBid: (product: Product) => void
  onRetractBid: (product: Product) => void
  onViewComments: (product: Product) => void
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
const RunProductItem = memo(({ product, runState, canBid, onPlaceBid, onRetractBid, onViewComments, getUserInitials }: RunProductItemProps) => {
  const { t } = useTranslation(['run'])

  const needsAdjustment = runState === 'adjusting' &&
                          product.purchased_quantity !== null &&
                          product.purchased_quantity > 0 &&
                          product.total_quantity !== product.purchased_quantity
  const needsAdjustmentShortage = needsAdjustment && product.purchased_quantity < product.total_quantity
  const needsAdjustmentSurplus = needsAdjustment && product.purchased_quantity > product.total_quantity
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

  // Calculate difference: positive = surplus, negative = shortage
  const difference = product.purchased_quantity !== null ? product.purchased_quantity - product.total_quantity : 0
  const shortage = difference < 0 ? Math.abs(difference) : 0
  const surplus = difference > 0 ? difference : 0

  // Retraction rules in adjusting mode:
  // - If shortage: cannot retract (would worsen shortage)
  // - If surplus: cannot retract at all (need to increase bids, not reduce)
  const canRetract = !adjustmentOk && !(
    runState === 'adjusting' &&
    product.current_user_bid &&
    !product.current_user_bid.interested_only &&
    (shortage > 0 || surplus > 0)
  )

  // Count comments
  const commentCount = product.user_bids.filter(bid => bid.comment && bid.comment.trim().length > 0).length

  // Show comments button logic:
  // - Before confirmed: always show (can add/edit)
  // - After confirmed: only show if there are comments (read-only)
  const canEditComments = runState === 'planning' || runState === 'active' || runState === 'adjusting'
  const showCommentsButton = canEditComments || commentCount > 0

  return (
    <div className={`product-item ${needsAdjustmentShortage ? 'needs-adjustment-shortage' : needsAdjustmentSurplus ? 'needs-adjustment-surplus' : adjustmentOk ? 'adjustment-ok' : notPurchasedAdjusting ? 'not-purchased-adjusting' : ''} ${fullyPurchased ? 'adjustment-ok' : partiallyPurchased ? 'needs-adjustment' : notPurchasedFinal ? 'not-purchased-adjusting' : ''}`}>
      <div className="product-header">
        <div className="product-title-row">
          <h4>{product.name}</h4>
          {showCommentsButton && (
            <button
              onClick={() => onViewComments(product)}
              className="comments-button"
              title={commentCount > 0 ? t('run:product.viewComments', { count: commentCount }) : t('run:product.addOrViewComments')}
            >
              🗩️
              {commentCount > 0 && <span className="comment-badge">{commentCount}</span>}
            </button>
          )}
        </div>
        {product.current_price && <span className="product-price">{product.current_price} RSD</span>}
      </div>

      {runState === 'adjusting' && (
        <div>
          {product.purchased_quantity !== null && product.purchased_quantity > 0 ? (
            <div className={`adjustment-info ${needsAdjustmentShortage ? 'needs-adjustment-shortage' : needsAdjustmentSurplus ? 'needs-adjustment-surplus' : 'adjustment-ok'}`}>
              <strong>{t('run:product.purchased')}:</strong> {product.purchased_quantity}{product.unit ? ` ${product.unit}` : ''} | <strong>{t('run:product.requested')}:</strong> {product.total_quantity}{product.unit ? ` ${product.unit}` : ''}
              {needsAdjustmentShortage && (
                <span className="adjustment-warning">
                  ⚠ {t('run:product.reduceBy', { amount: product.total_quantity - product.purchased_quantity, unit: product.unit || '' })}
                </span>
              )}
              {needsAdjustmentSurplus && (
                <span className="adjustment-warning surplus">
                  ⚠ {t('run:product.increaseBy', { amount: product.purchased_quantity - product.total_quantity, unit: product.unit || '' })}
                </span>
              )}
              {adjustmentOk && (
                <span className="adjustment-ok-badge">
                  ✓ {t('run:product.ok')}
                </span>
              )}
            </div>
          ) : (
            <div className="adjustment-info not-purchased-info">
              <strong>{t('run:product.notPurchased')}</strong>
              <span className="not-purchased-badge">
                ❌ {t('run:product.notPurchased')}
              </span>
            </div>
          )}
        </div>
      )}

      {isPostShopping && (
        <div>
          {(fullyPurchased || partiallyPurchased) && (
            <div className={`adjustment-info ${fullyPurchased ? 'adjustment-ok' : 'needs-adjustment'}`}>
              <strong>{t('run:product.purchased')}:</strong> {product.purchased_quantity}{product.unit ? ` ${product.unit}` : ''} | <strong>{t('run:product.requested')}:</strong> {product.total_quantity}{product.unit ? ` ${product.unit}` : ''}
              {fullyPurchased && (
                <span className="adjustment-ok-badge">
                  ✓ {t('run:product.ok')}
                </span>
              )}
              {partiallyPurchased && (
                <span className="adjustment-warning">
                  ⚠️ {t('run:product.partiallyPurchased')}
                </span>
              )}
            </div>
          )}
          {notPurchasedFinal && (
            <div className="adjustment-info not-purchased-info">
              <strong>{t('run:product.notPurchased')}</strong>
              <span className="not-purchased-badge">
                ❌ {t('run:product.notPurchased')}
              </span>
            </div>
          )}
        </div>
      )}

      <div className="product-stats">
        <div className="stat">
          <span className="stat-value">{product.total_quantity}{product.unit ? ` ${product.unit}` : ''}</span>
          <span className="stat-label">{t('run:product.totalQuantity')}</span>
        </div>
        <div className="stat">
          <span className="stat-value">{product.interested_count}</span>
          <span className="stat-label">{t('run:product.peopleInterested')}</span>
        </div>
      </div>

      <div className="bid-users">
        <h5>{t('run:product.bidders')}:</h5>
        <div className="user-avatars">
          {product.user_bids.map((bid, index) => {
            const allBidderNames = product.user_bids.map(b => b.user_name)
            return (
            <div key={`${bid.user_id}-${index}`} className="user-avatar" title={`${bid.user_name}: ${bid.interested_only ? t('run:product.interested') : `${bid.quantity}${product.unit ? ` ${product.unit}` : ''}`}`}>
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
                    {t('run:product.yourBid')}: {product.current_user_bid.interested_only ? t('run:product.interested') : `${product.current_user_bid.quantity}${product.unit ? ` ${product.unit}` : ''}`}
                  </span>
                  <div className="bid-buttons">
                    <button
                      onClick={() => onPlaceBid(product)}
                      className="edit-bid-button"
                      title={t('run:product.editBid')}
                    >
                      ✏️
                    </button>
                    {canRetract && (
                      <button
                        onClick={() => onRetractBid(product)}
                        className="retract-bid-button"
                        title={t('run:product.retractBid')}
                      >
                        −
                      </button>
                    )}
                  </div>
                </div>
              ) : product.current_user_bid && (adjustmentOk || notPurchasedAdjusting) ? (
                <div className="user-bid-status">
                  <span className="current-bid">
                    {t('run:product.yourBid')}: {product.current_user_bid.interested_only ? t('run:product.interested') : `${product.current_user_bid.quantity}${product.unit ? ` ${product.unit}` : ''}`}
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
                    {t('run:product.yourBid')}: {product.current_user_bid.interested_only ? t('run:product.interested') : `${product.current_user_bid.quantity}${product.unit ? ` ${product.unit}` : ''}`}
                  </span>
                  <div className="bid-buttons">
                    <button
                      onClick={() => onPlaceBid(product)}
                      className="edit-bid-button"
                      title={t('run:product.editBid')}
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => onRetractBid(product)}
                      className="retract-bid-button"
                      title={t('run:product.retractBid')}
                    >
                      −
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => onPlaceBid(product)}
                  className="place-bid-button"
                  title={t('run:product.placeBid')}
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
