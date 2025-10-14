import { useState, useEffect, useCallback, lazy, Suspense } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import '../styles/components/RunPage.css'
import '../styles/run-states.css'
import { WS_BASE_URL } from '../config'
import { runsApi, reassignmentApi } from '../api'
import type { RunDetail } from '../api'
import type { AvailableProduct, LeaderReassignmentRequest } from '../types'
import ErrorBoundary from './ErrorBoundary'

// Lazy load popup components for better code splitting
const BidPopup = lazy(() => import('./BidPopup'))
const AddProductPopup = lazy(() => import('./AddProductPopup'))
const ReassignLeaderPopup = lazy(() => import('./ReassignLeaderPopup'))
import RunProductItem from './RunProductItem'
import { useWebSocket } from '../hooks/useWebSocket'
import { getStateDisplay } from '../utils/runStates'
import Toast from './Toast'
import ConfirmDialog from './ConfirmDialog'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { useNotifications } from '../contexts/NotificationContext'
import { useRun, runKeys, useToggleReady, useStartShopping, useFinishAdjusting } from '../hooks/queries'
import { useAuth } from '../contexts/AuthContext'
import { handleError, formatErrorForDisplay } from '../utils/errorHandling'

// Using RunDetail type from API layer
type Product = RunDetail['products'][0]

// ProductItem component extracted to RunProductItem.tsx
// RunParticipants component extracted to RunParticipants.tsx

export default function RunPage() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()

  // Redirect if no runId or user
  if (!runId || !user) {
    navigate('/')
    return null
  }

  const userId = user.id

  // Use React Query for run data
  const { data: run, isLoading: loading, error: queryError } = useRun(runId)
  const queryClient = useQueryClient()
  const toggleReadyMutation = useToggleReady(runId)
  const startShoppingMutation = useStartShopping(runId)
  const finishAdjustingMutation = useFinishAdjusting(runId)

  const error = queryError instanceof Error ? queryError.message : ''

  const [showBidPopup, setShowBidPopup] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [showAddProductPopup, setShowAddProductPopup] = useState(false)
  const [showReassignPopup, setShowReassignPopup] = useState(false)
  const [reassignmentRequest, setReassignmentRequest] = useState<LeaderReassignmentRequest | null>(null)
  const { toast, showToast, hideToast } = useToast()
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()
  const { refreshUnreadCount } = useNotifications()

  const fetchReassignmentRequest = useCallback(async () => {
    try {
      const response = await reassignmentApi.getRunRequest(runId)
      setReassignmentRequest(response.request)
    } catch (err) {
      // Silently fail - not critical
      handleError('Fetch reassignment request', err)
    }
  }, [runId])

  useEffect(() => {
    fetchReassignmentRequest()
  }, [runId, fetchReassignmentRequest])

  const handleAcceptReassignment = async () => {
    if (!reassignmentRequest) return
    try {
      await reassignmentApi.acceptReassignment(reassignmentRequest.id)
      showToast('Leadership accepted!', 'success')
      setReassignmentRequest(null)
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'accept reassignment'), 'error')
    }
  }

  const handleDeclineReassignment = async () => {
    if (!reassignmentRequest) return
    try {
      await reassignmentApi.declineReassignment(reassignmentRequest.id)
      showToast('Request declined', 'success')
      setReassignmentRequest(null)
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'decline reassignment'), 'error')
    }
  }

  // WebSocket for real-time updates
  const handleWebSocketMessage = useCallback((message: any) => {
    if (!run) return

    // For all WebSocket messages, invalidate the run query to refetch
    // This is simpler than manual state updates and ensures data consistency
    if (message.type === 'bid_updated' || message.type === 'bid_retracted' ||
        message.type === 'ready_toggled' || message.type === 'state_changed' ||
        message.type === 'participant_removed') {
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
    } else if (message.type === 'reassignment_requested') {
      // Reassignment request created - fetch request for all participants
      fetchReassignmentRequest()
      if (message.data.to_user_id === userId) {
        showToast('You have a new leadership transfer request', 'info')
        refreshUnreadCount()
      }
    } else if (message.type === 'reassignment_accepted') {
      // Reassignment accepted - clear request and refresh run
      setReassignmentRequest(null)
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      showToast('Leadership has been transferred', 'success')
      refreshUnreadCount()
    } else if (message.type === 'reassignment_declined') {
      // Reassignment declined - clear request
      setReassignmentRequest(null)
      if (message.data.from_user_id === userId) {
        showToast('Leadership transfer request was declined', 'info')
        refreshUnreadCount()
      }
    }
  }, [run, userId, showToast, fetchReassignmentRequest, queryClient, runId, refreshUnreadCount])

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
      showToast(formatErrorForDisplay(err, 'retract bid'), 'error')
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
      showToast(formatErrorForDisplay(err, 'place bid'), 'error')
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
      brand: product.brand || null,
      current_price: product.current_price,
      total_quantity: 0,
      interested_count: 0,
      user_bids: [],
      current_user_bid: null,
      purchased_quantity: null
    }

    setSelectedProduct(fullProduct)
    setShowBidPopup(true)
  }

  const handleCancelAddProduct = () => {
    setShowAddProductPopup(false)
  }

  const handleToggleReady = async () => {
    try {
      await toggleReadyMutation.mutateAsync()
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'update ready status'), 'error')
    }
  }

  const handleStartShopping = async () => {
    try {
      await startShoppingMutation.mutateAsync()
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'start shopping'), 'error')
    }
  }

  const handleFinishAdjusting = async () => {
    try {
      await finishAdjustingMutation.mutateAsync()
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'finish adjusting'), 'error')
    }
  }

  const handleCancelRun = () => {
    const cancelAction = async () => {
      try {
        await runsApi.cancelRun(runId)
        showToast('Run cancelled successfully', 'success')
        // Refresh the run data to show updated state
        queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      } catch (err) {
        showToast(formatErrorForDisplay(err, 'cancel run'), 'error')
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
          <button onClick={() => navigate('/')} className="back-button">
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
          <button onClick={() => navigate('/')} className="back-button">
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
          <button onClick={() => navigate('/')} className="back-button">
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
        <span className="breadcrumb-link" onClick={() => navigate(`/groups/${run.group_id}`)}>
          {run.group_name}
        </span>
        {' > '}
        <Link to={`/stores/${run.store_id}`} className="breadcrumb-link">
          {run.store_name}
        </Link>
      </div>

      <div className="run-header">
        <div className="run-title">
          <h2>
            <Link to={`/stores/${run.store_id}`} className="store-link">
              {run.store_name}
            </Link>
          </h2>
          <span className={`run-state state-${run.state}`}>
            {stateDisplay.label}
          </span>
        </div>
      </div>

      {/* Reassignment banner for target user */}
      {reassignmentRequest && reassignmentRequest.to_user_id === userId && (
        <div className="alert alert-warning reassignment-banner">
          <div className="reassignment-content">
            <strong>{reassignmentRequest.from_user_name}</strong> wants to transfer leadership to you.
          </div>
          <div className="reassignment-actions">
            <button onClick={handleAcceptReassignment} className="btn btn-success btn-sm">
              Accept
            </button>
            <button onClick={handleDeclineReassignment} className="btn btn-secondary btn-sm">
              Decline
            </button>
          </div>
        </div>
      )}

      <div className="run-info">
        <div className="info-card">
          <h3>Run Information</h3>
          <div className="info-grid">
            <div className="info-item">
              <label>Leader:</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className={run.participants.find(p => p.is_leader)?.is_removed ? 'removed-user' : ''}>
                  {run.participants.find(p => p.is_leader)?.user_name || 'Unknown'}
                </span>
                {run.current_user_is_leader && run.state !== 'completed' && run.state !== 'cancelled' && run.participants.length > 1 && (
                  <button
                    onClick={() => setShowReassignPopup(true)}
                    className="btn btn-ghost btn-sm"
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                    disabled={reassignmentRequest !== null}
                    title={reassignmentRequest ? 'Reassignment request pending' : 'Reassign leadership'}
                  >
                    {reassignmentRequest ? 'Pending...' : 'Reassign'}
                  </button>
                )}
              </div>
            </div>
            <div className="info-item">
              <label>Status:</label>
              <span>{stateDisplay.description}</span>
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
                      <span className={`participant-name ${participant.is_removed ? 'removed-user' : ''}`}>
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
                    disabled={toggleReadyMutation.isPending}
                  />
                  <span>
                    {toggleReadyMutation.isPending ? 'Updating...' : "I'm ready (my order is complete)"}
                  </span>
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
              disabled={startShoppingMutation.isPending}
            >
              {startShoppingMutation.isPending ? '⏳ Starting...' : '🛒 Start Shopping'}
            </button>
            <p className="ready-hint">
              Click this button when you're heading to the store to begin the shopping phase.
            </p>
          </div>
        )}

        {run.state === 'shopping' && run.current_user_is_leader && (
          <div className="info-card">
            <h3>Shopping in Progress</h3>
            <p>You are currently shopping for this run.</p>
            <button
              onClick={() => navigate(`/shopping/${runId}`)}
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
              disabled={finishAdjustingMutation.isPending}
            >
              {finishAdjustingMutation.isPending ? '⏳ Processing...' : '✓ Finish Adjusting'}
            </button>
            <p className="ready-hint">
              Click when all bid totals match purchased quantities.
            </p>
          </div>
        )}

        {run.state === 'distributing' && (
          <div className="info-card">
            <h3>Distribution in Progress</h3>
            <p>Shopping is complete. Time to distribute items to participants.</p>
            <button
              onClick={() => navigate(`/distribution/${runId}`)}
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
          {canBid && run.state !== 'adjusting' && (
            <button onClick={handleAddProduct} className="add-product-button">
              + Add Product
            </button>
          )}
        </div>

        {run.products.length === 0 ? (
          <div className="no-products">
            <p>No products have been added to this run yet.</p>
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
                  <RunProductItem
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

      <Suspense fallback={null}>
        {showBidPopup && selectedProduct && (() => {
          const isAdjustingMode = run?.state === 'adjusting'
          const currentBid = selectedProduct.current_user_bid
          const hasPurchasedQuantity = selectedProduct.purchased_quantity !== null

          const shortage = hasPurchasedQuantity && selectedProduct.purchased_quantity !== null
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

        {showReassignPopup && run && (
          <ReassignLeaderPopup
            runId={runId}
            participants={run.participants.map(p => ({
              user_id: p.user_id,
              user_name: p.user_name,
              is_leader: p.is_leader,
            }))}
            onClose={() => setShowReassignPopup(false)}
            onSuccess={() => {
              showToast('Reassignment request sent!', 'success')
              fetchReassignmentRequest()
            }}
            onCancelRun={run.state !== 'completed' && run.state !== 'cancelled' ? handleCancelRun : undefined}
          />
        )}
      </Suspense>

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