import { useState, useEffect, useCallback, lazy, Suspense, useMemo } from 'react'
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
const ManageHelpersPopup = lazy(() => import('./ManageHelpersPopup'))
const ForceConfirmPopup = lazy(() => import('./ForceConfirmPopup'))
const CommentsPopup = lazy(() => import('./CommentsPopup'))
import RunProductItem from './RunProductItem'
import DownloadRunStateButton from './DownloadRunStateButton'
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
import { useDistribution, useMarkPickedUp, useCompleteDistribution, distributionKeys } from '../hooks/queries/useDistribution'
import type { DistributionUser } from '../schemas/distribution'

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

  // Distribution data (only fetched when in distributing or completed state)
  const shouldFetchDistribution = run?.state === 'distributing' || run?.state === 'completed'
  const { data: allUsers = [] } = useDistribution(runId, { enabled: shouldFetchDistribution })
  const markPickedUpMutation = useMarkPickedUp(runId)
  const completeDistributionMutation = useCompleteDistribution(runId)
  const [expandedUserId, setExpandedUserId] = useState<string | null>(null)

  const error = queryError instanceof Error ? queryError.message : ''

  const [showBidPopup, setShowBidPopup] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [showAddProductPopup, setShowAddProductPopup] = useState(false)
  const [showReassignPopup, setShowReassignPopup] = useState(false)
  const [showManageHelpersPopup, setShowManageHelpersPopup] = useState(false)
  const [showForceConfirmPopup, setShowForceConfirmPopup] = useState(false)
  const [showEditCommentPopup, setShowEditCommentPopup] = useState(false)
  const [showCommentsPopup, setShowCommentsPopup] = useState(false)
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
        message.type === 'participant_removed' || message.type === 'helper_toggled' ||
        message.type === 'comment_updated') {
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
    } else if (message.type === 'distribution_updated') {
      // Distribution update - refetch distribution data
      queryClient.invalidateQueries({ queryKey: distributionKeys.list(runId) })
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

  const handleSubmitBid = async (quantity: number, interestedOnly: boolean, comment: string | null) => {
    if (!selectedProduct) return

    try {
      await runsApi.placeBid(runId, {
        product_id: selectedProduct.id,
        quantity,
        interested_only: interestedOnly,
        comment
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

  const handleViewComments = (product: Product) => {
    setSelectedProduct(product)
    setShowCommentsPopup(true)
  }

  const handleCloseComments = () => {
    setShowCommentsPopup(false)
    setSelectedProduct(null)
  }

  const handleEditOwnBid = () => {
    // Close comments popup and open bid popup
    setShowCommentsPopup(false)
    setShowBidPopup(true)
    // selectedProduct is already set
  }

  const handlePlaceBidFromComments = () => {
    // Close comments popup and open bid popup
    setShowCommentsPopup(false)
    setShowBidPopup(true)
    // selectedProduct is already set
  }

  const getUserInitials = (name: string, allNames?: string[]) => {
    if (!name) return ''

    const firstInitial = name[0]?.toUpperCase() || ''

    // If allNames provided, check if first letter conflicts with others
    if (allNames && allNames.length > 1) {
      const firstLetters = allNames.map(n => n[0]?.toUpperCase() || '')
      const hasDuplicate = firstLetters.filter(l => l === firstInitial).length > 1

      if (hasDuplicate) {
        // Use first 2 characters if duplicate found
        return name.substring(0, 2).toUpperCase()
      }
    }

    // Default: use first letter only
    return firstInitial
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
      unit: null,
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
      await finishAdjustingMutation.mutateAsync(false)
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'finish adjusting'), 'error')
    }
  }

  const handleForceFinishAdjusting = () => {
    const forceFinishAction = async () => {
      try {
        await finishAdjustingMutation.mutateAsync(true)
        showToast('Moved to distribution!', 'success')
      } catch (err) {
        showToast(formatErrorForDisplay(err, 'force finish adjusting'), 'error')
      }
    }

    showConfirm(
      'Not all quantities have been adjusted. Items will be distributed proportionally based on each user\'s bid. For example, if you purchased 10 units but users bid for 15 total, each user will receive 2/3 of their original bid. Are you sure you want to proceed?',
      forceFinishAction,
      { danger: true }
    )
  }

  // Distribution handlers
  const handlePickup = async (bidId: string) => {
    try {
      await markPickedUpMutation.mutateAsync(bidId)
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'mark as picked up'), 'error')
    }
  }

  const handleMarkAllPickedUp = async (user: DistributionUser) => {
    try {
      const unpickedProducts = user.products.filter(p => !p.is_picked_up)
      for (const product of unpickedProducts) {
        await markPickedUpMutation.mutateAsync(product.bid_id)
      }
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'mark all as picked up'), 'error')
    }
  }

  const handleCompleteRun = async () => {
    try {
      await completeDistributionMutation.mutateAsync()
      showToast('Run completed successfully!', 'success')
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'complete run'), 'error')
    }
  }

  const toggleExpand = (userId: string) => {
    setExpandedUserId(expandedUserId === userId ? null : userId)
  }

  // Filter out users who have no purchased products
  const distributionUsers = useMemo(() => {
    console.log('Distribution raw data:', { allUsers, count: allUsers.length })
    const result = allUsers
      .map((user) => {
        const filteredProducts = user.products.filter(p => {
          console.log('Product filter:', {
            user: user.user_name,
            product: p.product_name,
            distributed_quantity: p.distributed_quantity,
            type: typeof p.distributed_quantity,
            passes: p.distributed_quantity && p.distributed_quantity > 0
          })
          return p.distributed_quantity && p.distributed_quantity > 0
        })
        return {
          ...user,
          products: filteredProducts
        }
      })
      .filter((user) => user.products.length > 0)
    console.log('Distribution filtered result:', { result, count: result.length })
    return result
  }, [allUsers])

  const allPickedUp = distributionUsers.length > 0 && distributionUsers.every(user => user.all_picked_up)
  const isLeaderOrHelper = run?.current_user_is_leader || run?.current_user_is_helper

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
                  <>
                    <button
                      onClick={() => setShowReassignPopup(true)}
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                      disabled={reassignmentRequest !== null}
                      title={reassignmentRequest ? 'Reassignment request pending' : 'Reassign leadership'}
                    >
                      {reassignmentRequest ? 'Pending...' : 'Reassign'}
                    </button>
                    {run.state === 'active' && (
                      <button
                        onClick={() => setShowForceConfirmPopup(true)}
                        className="btn btn-ghost btn-sm"
                        style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                        title="Force confirm run without waiting for all participants"
                      >
                        Force Confirm
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
            <div className="info-item">
              <label>Helpers:</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>{run.helpers.length > 0 ? run.helpers.join(', ') : 'None'}</span>
                {run.current_user_is_leader && run.state !== 'completed' && run.state !== 'cancelled' && (
                  <button
                    onClick={() => setShowManageHelpersPopup(true)}
                    className="btn btn-ghost btn-sm"
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                    title="Manage helpers"
                  >
                    Manage
                  </button>
                )}
              </div>
            </div>
            {run.comment && (
              <div className="info-item" style={{ gridColumn: '1 / -1' }}>
                <label>Comment:</label>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                  <span style={{ flex: 1 }}>{run.comment}</span>
                  {run.current_user_is_leader && run.state !== 'completed' && run.state !== 'cancelled' && (
                    <button
                      onClick={() => setShowEditCommentPopup(true)}
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                      title="Edit comment"
                    >
                      Edit
                    </button>
                  )}
                </div>
              </div>
            )}
            {!run.comment && run.current_user_is_leader && run.state !== 'completed' && run.state !== 'cancelled' && (
              <div className="info-item" style={{ gridColumn: '1 / -1' }}>
                <button
                  onClick={() => setShowEditCommentPopup(true)}
                  className="btn btn-secondary btn-sm"
                  style={{ fontSize: '0.875rem' }}
                >
                  + Add Comment
                </button>
              </div>
            )}
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
                        {participant.is_helper && <span className="helper-badge">Helper</span>}
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
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                onClick={handleStartShopping}
                className="btn btn-primary btn-lg"
                disabled={startShoppingMutation.isPending}
              >
                {startShoppingMutation.isPending ? '⏳ Starting...' : '🛒 Start Shopping'}
              </button>
              <DownloadRunStateButton
                runId={runId}
                storeName={run.store_name}
                className="btn btn-secondary btn-lg"
              />
            </div>
            <p className="ready-hint">
              Click this button when you're heading to the store to begin the shopping phase.
            </p>
          </div>
        )}

        {run.state === 'shopping' && (run.current_user_is_leader || run.current_user_is_helper) && (
          <div className="info-card">
            <h3>Shopping in Progress</h3>
            <p>You are currently shopping for this run.</p>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => navigate(`/shopping/${runId}`)}
                className="btn btn-success btn-lg"
              >
                📝 Open Shopping List
              </button>
              <DownloadRunStateButton
                runId={runId}
                storeName={run.store_name}
                className="btn btn-secondary btn-lg"
              />
            </div>
            <p className="ready-hint">
              Track prices and mark items as purchased.
            </p>
          </div>
        )}

        {run.state === 'adjusting' && run.current_user_is_leader && (
          <div className="info-card">
            <h3>Adjusting Bids</h3>
            <p>Some items had insufficient quantities. Participants need to reduce their bids until the total matches what was purchased.</p>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                onClick={handleFinishAdjusting}
                className="btn btn-primary btn-lg"
                disabled={finishAdjustingMutation.isPending}
              >
                {finishAdjustingMutation.isPending ? '⏳ Processing...' : '✓ Finish Adjusting'}
              </button>
              <button
                onClick={handleForceFinishAdjusting}
                className="btn btn-secondary btn-lg"
                disabled={finishAdjustingMutation.isPending}
              >
                Force Finish
              </button>
              <DownloadRunStateButton
                runId={runId}
                storeName={run.store_name}
                className="btn btn-secondary btn-lg"
              />
            </div>
            <p className="ready-hint">
              Click "Finish Adjusting" when all bid totals match purchased quantities, or "Force Finish" to proceed anyway.
            </p>
          </div>
        )}

      </div>

      {/* Distribution Section - shown in distributing and completed states */}
      {shouldFetchDistribution && (
        <div className="distribution-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3>Distribution</h3>
            {(run.current_user_is_leader || run.current_user_is_helper) && (
              <DownloadRunStateButton
                runId={runId}
                storeName={run.store_name}
                className="btn btn-secondary"
              />
            )}
          </div>
          {distributionUsers.length === 0 ? (
            <div className="empty-state">
              <p>No items to distribute. Either no products were purchased or no users have allocated items.</p>
            </div>
          ) : (
            <div className="distribution-list">
              {distributionUsers.map(user => (
              <div key={user.user_id} className={`user-card ${user.all_picked_up ? 'completed' : ''}`}>
                <div
                  className="user-header"
                  onClick={() => toggleExpand(user.user_id)}
                >
                  <div className="user-info">
                    <span className="user-name">{user.user_name}</span>
                    <span className="user-total">{user.total_cost} RSD</span>
                  </div>
                  <div className="user-actions">
                    {user.all_picked_up && <span className="pickup-badge">✓ Picked up</span>}
                    <span className="expand-icon">{expandedUserId === user.user_id ? '▼' : '▶'}</span>
                  </div>
                </div>

                {expandedUserId === user.user_id && (
                  <div className="user-products">
                    <div className="user-products-header">
                      {!user.all_picked_up && isLeaderOrHelper && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleMarkAllPickedUp(user)
                          }}
                          className="mark-all-button"
                          disabled={markPickedUpMutation.isPending}
                        >
                          {markPickedUpMutation.isPending ? '⏳ Updating...' : 'Mark All Picked Up'}
                        </button>
                      )}
                    </div>
                    {user.products.map(product => (
                      <div key={product.bid_id} className={`product-item ${product.is_picked_up ? 'picked-up' : ''}`}>
                        <div className="product-info">
                          <div className="product-name">
                            {product.product_name}
                            {product.distributed_quantity < product.requested_quantity && (
                              <span className="shortage-badge" title="Quantity reduced due to shortage">⚠️</span>
                            )}
                          </div>
                          <div className="product-details">
                            <span>Requested: {product.requested_quantity}{product.product_unit ? ` ${product.product_unit}` : ''}</span>
                            <span>Allocated: {product.distributed_quantity}{product.product_unit ? ` ${product.product_unit}` : ''}</span>
                            <span>@{product.price_per_unit} RSD</span>
                            <span className="product-subtotal">{product.subtotal} RSD</span>
                          </div>
                        </div>
                        {isLeaderOrHelper && (
                          <button
                            onClick={() => handlePickup(product.bid_id)}
                            disabled={product.is_picked_up || markPickedUpMutation.isPending}
                            className={`pickup-button ${product.is_picked_up ? 'picked-up' : ''}`}
                          >
                            {markPickedUpMutation.isPending ? '⏳ Updating...' : product.is_picked_up ? '✓ Picked up' : 'Mark Picked Up'}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            </div>
          )}

          {allPickedUp && isLeaderOrHelper && run?.state === 'distributing' && (
            <div className="complete-section">
              <button
                onClick={handleCompleteRun}
                className="complete-button"
                disabled={completeDistributionMutation.isPending}
              >
                {completeDistributionMutation.isPending ? '⏳ Completing...' : 'Complete Run'}
              </button>
            </div>
          )}
        </div>
      )}

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
                    onViewComments={handleViewComments}
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
              currentComment={currentBid?.comment}
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

        {showCommentsPopup && selectedProduct && (
          <CommentsPopup
            productName={selectedProduct.name}
            userBids={selectedProduct.user_bids}
            currentUserId={userId}
            onClose={handleCloseComments}
            onEditOwnBid={handleEditOwnBid}
            onPlaceBid={handlePlaceBidFromComments}
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

        {showManageHelpersPopup && run && (
          <ManageHelpersPopup
            run={run}
            onClose={() => setShowManageHelpersPopup(false)}
          />
        )}

        {showForceConfirmPopup && (
          <ForceConfirmPopup
            runId={runId}
            onClose={() => setShowForceConfirmPopup(false)}
            onSuccess={() => {
              setShowForceConfirmPopup(false)
              showToast('Run force confirmed!', 'success')
              queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
            }}
          />
        )}
      </Suspense>

      {showEditCommentPopup && run && (
        <EditCommentPopup
          runId={runId}
          currentComment={run.comment || ''}
          onClose={() => setShowEditCommentPopup(false)}
          onSuccess={() => {
            setShowEditCommentPopup(false)
            showToast('Comment updated!', 'success')
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
          danger={confirmState.danger}
        />
      )}
    </div>
  )
}

// EditCommentPopup component
function EditCommentPopup({
  runId,
  currentComment,
  onClose,
  onSuccess
}: {
  runId: string
  currentComment: string
  onClose: () => void
  onSuccess: () => void
}) {
  const [comment, setComment] = useState(currentComment)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const queryClient = useQueryClient()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await runsApi.updateComment(runId, { comment: comment.trim() || null })
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update comment')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-sm" onClick={e => e.stopPropagation()}>
        <h3>Edit Comment</h3>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="comment" className="form-label">Comment</label>
            <textarea
              id="comment"
              className="form-input"
              value={comment}
              onChange={e => setComment(e.target.value)}
              placeholder="e.g., Bringing cooler, Meeting at 2pm"
              disabled={loading}
              maxLength={500}
              rows={3}
              autoFocus
            />
            <span className="char-counter">{comment.length}/500</span>
          </div>
          <div className="button-group">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}