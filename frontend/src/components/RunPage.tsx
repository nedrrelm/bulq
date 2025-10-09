import { useState, useEffect, memo, useCallback } from 'react'
import './RunPage.css'
import '../styles/run-states.css'
import { WS_BASE_URL } from '../config'
import { runsApi, ApiError } from '../api'
import type { RunDetail } from '../api'
import type { AvailableProduct } from '../types/product'
import BidPopup from './BidPopup'
import AddProductPopup from './AddProductPopup'
import ErrorBoundary from './ErrorBoundary'
import { useWebSocket } from '../hooks/useWebSocket'
import { getStateDisplay } from '../utils/runStates'
import Toast from './Toast'
import ConfirmDialog from './ConfirmDialog'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'

// Using RunDetail type from API layer
type Product = RunDetail['products'][0]
type UserBid = Product['user_bids'][0]
type Participant = RunDetail['participants'][0]

interface RunPageProps {
  runId: string
  userId: string
  onBack: (groupId?: string) => void
  onShoppingSelect?: (runId: string) => void
  onDistributionSelect?: (runId: string) => void
}

interface ProductItemProps {
  product: Product
  runState: string
  canBid: boolean
  onPlaceBid: (product: Product) => void
  onRetractBid: (product: Product) => void
  getUserInitials: (name: string) => string
}

const ProductItem = memo(({ product, runState, canBid, onPlaceBid, onRetractBid, getUserInitials }: ProductItemProps) => {
  const needsAdjustment = runState === 'adjusting' &&
                          product.purchased_quantity !== null &&
                          product.total_quantity > product.purchased_quantity
  const adjustmentOk = runState === 'adjusting' &&
                       product.purchased_quantity !== null &&
                       product.total_quantity === product.purchased_quantity

  const shortage = product.purchased_quantity !== null ? product.total_quantity - product.purchased_quantity : 0
  const canRetract = !adjustmentOk && !(runState === 'adjusting' && product.current_user_bid && !product.current_user_bid.interested_only && product.current_user_bid.quantity > shortage)

  return (
    <div className={`product-item ${needsAdjustment ? 'needs-adjustment' : adjustmentOk ? 'adjustment-ok' : ''}`}>
      <div className="product-header">
        <h4>{product.name}</h4>
        <span className="product-price">${product.base_price}</span>
      </div>

      {runState === 'adjusting' && product.purchased_quantity !== null && (
        <div className={`adjustment-info ${needsAdjustment ? 'needs-adjustment' : 'adjustment-ok'}`}>
          <strong>Purchased:</strong> {product.purchased_quantity} | <strong>Requested:</strong> {product.total_quantity}
          {needsAdjustment && (
            <span className="adjustment-warning">
              ⚠ Reduce by {product.total_quantity - product.purchased_quantity}
            </span>
          )}
          {adjustmentOk && (
            <span className="adjustment-ok-badge">
              ✓ OK
            </span>
          )}
        </div>
      )}

      <div className="product-stats">
        <div className="stat">
          <span className="stat-value">{product.total_quantity}</span>
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
          {product.user_bids.map((bid, index) => (
            <div key={`${bid.user_id}-${index}`} className="user-avatar" title={`${bid.user_name}: ${bid.interested_only ? 'Interested' : `${bid.quantity} items`}`}>
              <span className="avatar-initials">{getUserInitials(bid.user_name)}</span>
              <span className="bid-quantity">
                {bid.interested_only ? '?' : bid.quantity}
              </span>
            </div>
          ))}
        </div>
      </div>

      {canBid && (
        <div className="bid-actions">
          {product.current_user_bid ? (
            <div className="user-bid-status">
              <span className="current-bid">
                Your bid: {product.current_user_bid.interested_only ? 'Interested' : `${product.current_user_bid.quantity} items`}
              </span>
              <div className="bid-buttons">
                <button
                  onClick={() => onPlaceBid(product)}
                  className="edit-bid-button"
                  title={adjustmentOk ? "No adjustment needed" : "Edit bid"}
                  disabled={adjustmentOk}
                  style={adjustmentOk ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
                >
                  ✏️
                </button>
                <button
                  onClick={() => onRetractBid(product)}
                  className="retract-bid-button"
                  title={!canRetract ? "Cannot fully retract - would remove more than needed" : adjustmentOk ? "No adjustment needed" : "Retract bid"}
                  disabled={!canRetract}
                  style={!canRetract ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
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

export default function RunPage({ runId, userId, onBack, onShoppingSelect, onDistributionSelect }: RunPageProps) {
  const [run, setRun] = useState<RunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showBidPopup, setShowBidPopup] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [showAddProductPopup, setShowAddProductPopup] = useState(false)
  const { toast, showToast, hideToast } = useToast()
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

  const fetchRunDetails = async (silent = false) => {
    try {
      if (!silent) {
        setLoading(true)
      }
      setError('')

      const runData = await runsApi.getRunDetails(runId)
      setRun(runData)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to load run details')
    } finally {
      if (!silent) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    fetchRunDetails()
  }, [runId])

  // WebSocket for real-time updates
  const handleWebSocketMessage = useCallback((message: any) => {
    if (!run) return

    if (message.type === 'bid_updated') {
          // Update product with new bid or updated bid
          setRun(prev => {
            if (!prev) return prev

            // Check if product exists in the run
            const productExists = prev.products.some(p => p.id === message.data.product_id)

            // If product doesn't exist (newly added), refetch run details
            if (!productExists) {
              fetchRunDetails(true)
              return prev
            }

            return {
              ...prev,
              products: prev.products.map(p => {
                if (p.id === message.data.product_id) {
                  // Check if bid from this user already exists
                  const existingBidIndex = p.user_bids.findIndex(b => b.user_id === message.data.user_id)
                  let newUserBids = [...p.user_bids]

                  const newBid: UserBid = {
                    user_id: message.data.user_id,
                    user_name: message.data.user_name,
                    quantity: message.data.quantity,
                    interested_only: message.data.interested_only
                  }

                  if (existingBidIndex >= 0) {
                    // Update existing bid
                    newUserBids[existingBidIndex] = newBid
                  } else {
                    // Add new bid
                    newUserBids.push(newBid)
                  }

                  // Update current_user_bid if this is the current user's bid
                  const isCurrentUser = message.data.user_id === userId
                  const newCurrentUserBid = isCurrentUser ? newBid : p.current_user_bid

                  return {
                    ...p,
                    user_bids: newUserBids,
                    current_user_bid: newCurrentUserBid,
                    total_quantity: message.data.new_total,
                    interested_count: newUserBids.filter(b => b.interested_only || b.quantity > 0).length
                  }
                }
                return p
              })
            }
          })
        } else if (message.type === 'bid_retracted') {
          // Remove bid from product
          setRun(prev => {
            if (!prev) return prev
            return {
              ...prev,
              products: prev.products.map(p => {
                if (p.id === message.data.product_id) {
                  const newUserBids = p.user_bids.filter(b => b.user_id !== message.data.user_id)
                  const isCurrentUser = message.data.user_id === userId
                  return {
                    ...p,
                    user_bids: newUserBids,
                    current_user_bid: isCurrentUser ? null : p.current_user_bid,
                    total_quantity: message.data.new_total,
                    interested_count: newUserBids.filter(b => b.interested_only || b.quantity > 0).length
                  }
                }
                return p
              })
            }
          })
        } else if (message.type === 'ready_toggled') {
          // Update participant ready status and current user ready if it's them
          setRun(prev => {
            if (!prev) return prev

            const isCurrentUser = message.data.user_id === userId

            return {
              ...prev,
              participants: prev.participants.map(p =>
                p.user_id === message.data.user_id
                  ? { ...p, is_ready: message.data.is_ready }
                  : p
              ),
              current_user_is_ready: isCurrentUser ? message.data.is_ready : prev.current_user_is_ready
            }
          })
      } else if (message.type === 'state_changed') {
        // Update run state
        setRun(prev => {
          if (!prev) return prev
          return {
            ...prev,
            state: message.data.new_state
          }
        })
      }
  }, [run, userId])

  useWebSocket(
    runId ? `${WS_BASE_URL}/ws/runs/${runId}` : null,
    {
      onMessage: handleWebSocketMessage
    }
  )

  const canBid = run?.state === 'planning' || run?.state === 'active' || run?.state === 'adjusting'

  const handlePlaceBid = (product: Product) => {
    setSelectedProduct(product)
    setShowBidPopup(true)
  }

  const handleRetractBid = async (product: Product) => {
    try {
      await runsApi.retractBid(runId, product.id)
      // WebSocket will update the run data automatically
    } catch (err) {
      console.error('Error retracting bid:', err)
      showToast(err instanceof ApiError ? err.message : 'Failed to retract bid. Please try again.', 'error')
    }
  }

  const handleSubmitBid = async (quantity: number, interestedOnly: boolean) => {
    if (!selectedProduct) return

    try {
      await runsApi.placeBid(runId, {
        product_id: selectedProduct.id,
        quantity,
        interested_only: interestedOnly
      })

      // WebSocket will update the run data automatically
      setShowBidPopup(false)
      setSelectedProduct(null)
    } catch (err) {
      console.error('Error placing bid:', err)
      showToast('Failed to place bid. Please try again.', 'error')
    }
  }

  const handleCancelBid = () => {
    setShowBidPopup(false)
    setSelectedProduct(null)
  }

  const getUserInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase()
  }

  const handleAddProduct = () => {
    setShowAddProductPopup(true)
  }

  const handleProductSelected = async (product: AvailableProduct) => {
    setShowAddProductPopup(false)

    // Convert available product to full product format and open bid popup
    const fullProduct: Product = {
      id: product.id,
      name: product.name,
      base_price: product.base_price,
      total_quantity: 0,
      interested_count: 0,
      user_bids: [],
      current_user_bid: null
    }

    setSelectedProduct(fullProduct)
    setShowBidPopup(true)
  }

  const handleCancelAddProduct = () => {
    setShowAddProductPopup(false)
  }

  const handleToggleReady = async () => {
    try {
      await runsApi.toggleReady(runId)
      // Refetch run data silently to avoid page jump
      await fetchRunDetails(true)
    } catch (err) {
      console.error('Error toggling ready:', err)
      showToast('Failed to update ready status. Please try again.', 'error')
    }
  }

  const handleStartShopping = async () => {
    try {
      await runsApi.startShopping(runId)
      // Refetch run data to ensure UI is updated
      await fetchRunDetails()
    } catch (err) {
      console.error('Error starting shopping:', err)
      showToast('Failed to start shopping. Please try again.', 'error')
    }
  }

  const handleFinishAdjusting = async () => {
    try {
      await runsApi.finishAdjusting(runId)
      // Refetch run data to ensure UI is updated
      await fetchRunDetails()
    } catch (err) {
      console.error('Error finishing adjusting:', err)
      showToast(err instanceof ApiError ? err.message : 'Failed to finish adjusting. Please try again.', 'error')
    }
  }

  const handleCancelRun = () => {
    const cancelAction = async () => {
      try {
        await runsApi.cancelRun(runId)
        showToast('Run cancelled successfully', 'success')
        // Navigate back to group page after a short delay
        setTimeout(() => {
          onBack(run?.group_id)
        }, 1500)
      } catch (err) {
        console.error('Error cancelling run:', err)
        showToast(err instanceof ApiError ? err.message : 'Failed to cancel run. Please try again.', 'error')
      }
    }

    showConfirm(
      'Are you sure you want to cancel this run? This action cannot be undone.',
      cancelAction,
      { danger: true }
    )
  }

  if (loading) {
    return (
      <div className="run-page">
        <div className="run-header">
          <button onClick={() => onBack(run?.group_id)} className="back-button">
            ← Back to Group
          </button>
          <h2>Loading run...</h2>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="run-page">
        <div className="run-header">
          <button onClick={() => onBack(run?.group_id)} className="back-button">
            ← Back to Group
          </button>
          <h2>Error</h2>
        </div>
        <div className="error">
          <p>❌ Failed to load run: {error}</p>
        </div>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="run-page">
        <div className="run-header">
          <button onClick={() => onBack(run?.group_id)} className="back-button">
            ← Back to Group
          </button>
          <h2>Run not found</h2>
        </div>
      </div>
    )
  }

  const stateDisplay = getStateDisplay(run.state)

  return (
    <div className="run-page">
      <div className="breadcrumb">
        <span className="breadcrumb-link" onClick={() => onBack(run.group_id)}>
          {run.group_name}
        </span>
        {' > '}
        <span>{run.store_name}</span>
      </div>

      <div className="run-header">
        <div className="run-title">
          <h2>{run.store_name}</h2>
          <span className={`run-state state-${run.state}`}>
            {stateDisplay.label}
          </span>
        </div>
        {run.current_user_is_leader && run.state !== 'completed' && run.state !== 'cancelled' && (
          <button
            onClick={handleCancelRun}
            className="btn btn-danger cancel-run-button"
            title="Cancel this run"
          >
            ✕ Cancel Run
          </button>
        )}
      </div>

      <div className="run-info">
        <div className="info-card">
          <h3>Run Information</h3>
          <div className="info-grid">
            <div className="info-item">
              <label>Group:</label>
              <span>{run.group_name}</span>
            </div>
            <div className="info-item">
              <label>Store:</label>
              <span>{run.store_name}</span>
            </div>
            <div className="info-item">
              <label>Leader:</label>
              <span>{run.participants.find(p => p.is_leader)?.user_name || 'Unknown'}</span>
            </div>
            <div className="info-item">
              <label>Status:</label>
              <span>{stateDisplay.description}</span>
            </div>
            <div className="info-item">
              <label>Run ID:</label>
              <span className="run-id">{run.id}</span>
            </div>
          </div>
        </div>

        {run.state === 'active' && (
          <ErrorBoundary>
            <div className="info-card">
              <h3>Participants</h3>
              <div className="participants-list">
                {run.participants.map(participant => (
                  <div key={participant.user_id} className="participant-item">
                    <div className="participant-info">
                      <span className="participant-name">
                        {participant.user_name}
                        {participant.is_leader && <span className="leader-badge">Leader</span>}
                      </span>
                    </div>
                    <div className="participant-ready">
                      {participant.is_ready ? (
                        <span className="ready-indicator ready">✓ Ready</span>
                      ) : (
                        <span className="ready-indicator not-ready">⏳ Not Ready</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <div className="ready-section">
                <label className="ready-checkbox">
                  <input
                    type="checkbox"
                    checked={run.current_user_is_ready}
                    onChange={handleToggleReady}
                  />
                  <span>I'm ready (my order is complete)</span>
                </label>
                <p className="ready-hint">When all participants are ready, the run will automatically move to confirmed state.</p>
              </div>
            </div>
          </ErrorBoundary>
        )}

        {run.state === 'confirmed' && run.current_user_is_leader && (
          <div className="info-card">
            <h3>Ready to Shop</h3>
            <p>All participants are ready! The shopping list is finalized.</p>
            <button
              onClick={handleStartShopping}
              className="btn btn-primary btn-lg"
            >
              🛒 Start Shopping
            </button>
            <p className="ready-hint">
              Click this button when you're heading to the store to begin the shopping phase.
            </p>
          </div>
        )}

        {run.state === 'shopping' && run.current_user_is_leader && onShoppingSelect && (
          <div className="info-card">
            <h3>Shopping in Progress</h3>
            <p>You are currently shopping for this run.</p>
            <button
              onClick={() => onShoppingSelect(runId)}
              className="btn btn-success btn-lg"
            >
              📝 Open Shopping List
            </button>
            <p className="ready-hint">
              Track prices and mark items as purchased.
            </p>
          </div>
        )}

        {run.state === 'adjusting' && run.current_user_is_leader && (
          <div className="info-card">
            <h3>Adjusting Bids</h3>
            <p>Some items had insufficient quantities. Participants need to reduce their bids until the total matches what was purchased.</p>
            <button
              onClick={handleFinishAdjusting}
              className="btn btn-primary btn-lg"
            >
              ✓ Finish Adjusting
            </button>
            <p className="ready-hint">
              Click when all bid totals match purchased quantities.
            </p>
          </div>
        )}

        {run.state === 'distributing' && onDistributionSelect && (
          <div className="info-card">
            <h3>Distribution in Progress</h3>
            <p>Shopping is complete. Time to distribute items to participants.</p>
            <button
              onClick={() => onDistributionSelect(runId)}
              className="btn btn-success btn-lg"
            >
              📦 Open Distribution
            </button>
            <p className="ready-hint">
              Track who picked up their items.
            </p>
          </div>
        )}
      </div>

      <div className="products-section">
        <div className="products-header">
          <h3>Products ({run.products.length})</h3>
          {canBid && (
            <button onClick={handleAddProduct} className="add-product-button">
              + Add Product
            </button>
          )}
        </div>

        {run.products.length === 0 ? (
          <div className="no-products">
            <p>No products have been added to this run yet.</p>
            {run.state === 'planning' && (
              <p>Users can start expressing interest in products to get this run started!</p>
            )}
          </div>
        ) : (
          <div className="products-list">
            {run.products
              .sort((a, b) => {
                // In adjusting state, sort by adjustment status
                if (run.state === 'adjusting') {
                  const aNeedsAdjustment = a.purchased_quantity !== null && a.total_quantity > a.purchased_quantity
                  const bNeedsAdjustment = b.purchased_quantity !== null && b.total_quantity > b.purchased_quantity

                  // Products needing adjustment come first
                  if (aNeedsAdjustment && !bNeedsAdjustment) return -1
                  if (!aNeedsAdjustment && bNeedsAdjustment) return 1
                }
                return 0
              })
              .map((product) => (
                <ErrorBoundary key={product.id}>
                  <ProductItem
                    product={product}
                    runState={run.state}
                    canBid={canBid}
                    onPlaceBid={handlePlaceBid}
                    onRetractBid={handleRetractBid}
                    getUserInitials={getUserInitials}
                  />
                </ErrorBoundary>
              ))}
          </div>
        )}
      </div>

      {run.state === 'active' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>💡 This run is currently active. Users can place bids and specify quantities for products they want.</p>
          </div>
        </div>
      )}

      {run.state === 'planning' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>📋 This run is in planning phase. Users can express interest in products to help plan the shopping list.</p>
          </div>
        </div>
      )}

      {run.state === 'confirmed' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>✅ This run has been confirmed! The shopping list is finalized and ready for execution.</p>
          </div>
        </div>
      )}

      {run.state === 'shopping' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>🛒 Shopping is in progress! Designated shoppers are executing the run.</p>
          </div>
        </div>
      )}

      {run.state === 'adjusting' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>⚠️ Some items had insufficient quantities. Please reduce your bids on highlighted products until totals match what was purchased.</p>
          </div>
        </div>
      )}

      {run.state === 'completed' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>🎉 This run has been completed! Costs have been calculated and the run is finished.</p>
          </div>
        </div>
      )}

      {showBidPopup && selectedProduct && (() => {
        const isAdjustingMode = run?.state === 'adjusting'
        const currentBid = selectedProduct.current_user_bid
        const hasPurchasedQuantity = selectedProduct.purchased_quantity !== null

        const shortage = hasPurchasedQuantity
          ? selectedProduct.total_quantity - selectedProduct.purchased_quantity
          : 0

        const minAllowed = isAdjustingMode && currentBid && hasPurchasedQuantity
          ? Math.max(0, currentBid.quantity - shortage)
          : undefined

        const maxAllowed = isAdjustingMode && currentBid
          ? currentBid.quantity
          : undefined

        return (
          <BidPopup
            productName={selectedProduct.name}
            currentQuantity={currentBid?.quantity}
            onSubmit={handleSubmitBid}
            onCancel={handleCancelBid}
            adjustingMode={isAdjustingMode}
            minAllowed={minAllowed}
            maxAllowed={maxAllowed}
          />
        )
      })()}

      {showAddProductPopup && (
        <AddProductPopup
          runId={runId}
          onProductSelected={handleProductSelected}
          onCancel={handleCancelAddProduct}
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
          danger={confirmState.danger}
        />
      )}
    </div>
  )
}