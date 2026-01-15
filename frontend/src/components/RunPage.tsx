import { useState, useEffect, useCallback, lazy, Suspense, useMemo } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import '../styles/components/RunPage.css'
import '../styles/run-states.css'
import { WS_BASE_URL } from '../config'
import { runsApi, reassignmentApi } from '../api'
import type { RunDetail } from '../api'
import type { AvailableProduct, LeaderReassignmentRequest } from '../types'
import ErrorBoundary from './ErrorBoundary'
import { getErrorMessage } from '../utils/errorHandling'

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
  const { t } = useTranslation(['common', 'run'])
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

  const error = getErrorMessage(queryError, '')

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
      showToast(t('run:messages.leadershipAccepted'), 'success')
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
      showToast(t('run:messages.requestDeclined'), 'success')
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
        showToast(t('run:messages.newLeadershipRequest'), 'info')
        refreshUnreadCount()
      }
    } else if (message.type === 'reassignment_accepted') {
      // Reassignment accepted - clear request and refresh run
      setReassignmentRequest(null)
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      showToast(t('run:messages.leadershipTransferred'), 'success')
      refreshUnreadCount()
    } else if (message.type === 'reassignment_declined') {
      // Reassignment declined - clear request
      setReassignmentRequest(null)
      if (message.data.from_user_id === userId) {
        showToast(t('run:messages.leadershipRequestDeclined'), 'info')
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
        showToast(t('run:messages.movedToDistribution'), 'success')
      } catch (err) {
        showToast(formatErrorForDisplay(err, 'force finish adjusting'), 'error')
      }
    }

    showConfirm(
      t('run:prompts.forceFinishAdjusting'),
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
      showToast(t('run:messages.runCompletedSuccessfully'), 'success')
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'complete run'), 'error')
    }
  }

  const toggleExpand = (userId: string) => {
    setExpandedUserId(expandedUserId === userId ? null : userId)
  }

  // Filter out users who have no purchased products
  const distributionUsers = useMemo(() => {
    // First, calculate total distributed quantities for each product across all users
    const productTotals = new Map<string, { total: number, remaining: number }>()

    allUsers.forEach(user => {
      user.products.forEach(product => {
        if (product.distributed_quantity && product.distributed_quantity > 0) {
          const existing = productTotals.get(product.product_id) || { total: 0, remaining: 0 }
          existing.total += product.distributed_quantity
          if (!product.is_picked_up) {
            existing.remaining += product.distributed_quantity
          }
          productTotals.set(product.product_id, existing)
        }
      })
    })

    const result = allUsers
      .map((user) => {
        const filteredProducts = user.products.filter(p => {
          return p.distributed_quantity && p.distributed_quantity > 0
        })

        // Add remaining/total info to each product
        const enrichedProducts = filteredProducts.map(p => {
          const totals = productTotals.get(p.product_id)
          return {
            ...p,
            remaining_total: totals?.remaining || 0,
            distributed_total: totals?.total || 0
          }
        })

        return {
          ...user,
          products: enrichedProducts
        }
      })
      .filter((user) => user.products.length > 0)
    return result
  }, [allUsers])

  const allPickedUp = distributionUsers.length > 0 && distributionUsers.every(user => user.all_picked_up)
  const isLeaderOrHelper = run?.current_user_is_leader || run?.current_user_is_helper

  // Calculate user breakdown from bids for pre-distribution states
  const userBreakdownFromBids = useMemo(() => {
    if (!run || shouldFetchDistribution) return []

    const breakdown = run.participants
      .map(participant => {
        const userProducts = run.products
          .map(product => {
            const bid = product.user_bids.find(b => b.user_id === participant.user_id)
            if (!bid || bid.interested_only) return null

            const price = product.current_price ? parseFloat(product.current_price) : 0
            const subtotal = price * bid.quantity

            return {
              product_id: product.id,
              product_name: product.name,
              product_unit: product.unit,
              quantity: bid.quantity,
              price_per_unit: price,
              subtotal: subtotal
            }
          })
          .filter((p): p is NonNullable<typeof p> => p !== null)

        const totalCost = userProducts.reduce((sum, p) => sum + p.subtotal, 0)

        return {
          user_id: participant.user_id,
          user_name: participant.user_name,
          products: userProducts,
          total_cost: totalCost.toFixed(2)
        }
      })
      .filter(user => user.products.length > 0)

    return breakdown
  }, [run, shouldFetchDistribution])

  // Calculate total run price based on state
  const runPriceSummary = useMemo(() => {
    if (!run) return null

    if (shouldFetchDistribution && distributionUsers.length > 0) {
      // Distributing/Completed: Use actual distribution data
      const finalTotal = distributionUsers.reduce((sum, user) => {
        return sum + parseFloat(user.total_cost)
      }, 0)
      return {
        type: 'final' as const,
        total: finalTotal
      }
    }

    if (run.state === 'shopping' || run.state === 'adjusting') {
      // Shopping/Adjusting: Show purchased + remaining estimate
      let purchasedTotal = 0
      let remainingEstimate = 0

      run.products.forEach(product => {
        const price = product.current_price ? parseFloat(product.current_price) : 0

        if (product.purchased_quantity !== null && product.purchased_quantity !== undefined) {
          // Product has been purchased
          purchasedTotal += price * product.purchased_quantity
        } else {
          // Product not yet purchased, estimate from bids
          const totalQuantity = product.user_bids
            .filter(bid => !bid.interested_only)
            .reduce((qty, bid) => qty + bid.quantity, 0)
          remainingEstimate += price * totalQuantity
        }
      })

      return {
        type: 'split' as const,
        purchased: purchasedTotal,
        remaining: remainingEstimate,
        total: purchasedTotal + remainingEstimate
      }
    }

    // Pre-shopping (planning, active, confirmed): Estimated total
    const estimatedTotal = run.products.reduce((sum, product) => {
      if (!product.current_price) return sum
      const price = parseFloat(product.current_price)
      const totalQuantity = product.user_bids
        .filter(bid => !bid.interested_only)
        .reduce((qty, bid) => qty + bid.quantity, 0)
      return sum + (price * totalQuantity)
    }, 0)

    return {
      type: 'estimated' as const,
      total: estimatedTotal
    }
  }, [run, shouldFetchDistribution, distributionUsers])

  const handleCancelRun = () => {
    const cancelAction = async () => {
      try {
        await runsApi.cancelRun(runId)
        showToast(t('run:messages.runCancelledSuccessfully'), 'success')
        // Refresh the run data to show updated state
        queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      } catch (err) {
        showToast(formatErrorForDisplay(err, 'cancel run'), 'error')
      }
    }

    showConfirm(
      t('run:prompts.cancelRun'),
      cancelAction,
      { danger: true }
    )
  }

  if (loading) {
    return (
      <div className="run-page">
        <div className="run-header">
          <button onClick={() => navigate('/')} className="back-button">
            {t('common:navigation.backToGroup')}
          </button>
          <h2>{t('run:messages.loadingRun')}</h2>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="run-page">
        <div className="run-header">
          <button onClick={() => navigate('/')} className="back-button">
            {t('common:navigation.backToGroup')}
          </button>
          <h2>{t('common:errors.error')}</h2>
        </div>
        <div className="error">
          <p>{t('run:errors.failedToLoadRun', { error })}</p>
        </div>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="run-page">
        <div className="run-header">
          <button onClick={() => navigate('/')} className="back-button">
            {t('common:navigation.backToGroup')}
          </button>
          <h2>{t('run:errors.runNotFound')}</h2>
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
            {t('run:messages.leadershipTransferRequest', { userName: reassignmentRequest.from_user_name })}
          </div>
          <div className="reassignment-actions">
            <button onClick={handleAcceptReassignment} className="btn btn-success btn-sm">
              {t('run:actions.accept')}
            </button>
            <button onClick={handleDeclineReassignment} className="btn btn-secondary btn-sm">
              {t('run:actions.decline')}
            </button>
          </div>
        </div>
      )}

      <div className="run-info">
        <div className="info-card">
          <h3>{t('run:labels.runInformation')}</h3>
          <div className="info-grid">
            <div className="info-item">
              <label>{t('run:labels.leader')}:</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span className={run.participants.find(p => p.is_leader)?.is_removed ? 'removed-user' : ''}>
                  {run.participants.find(p => p.is_leader)?.user_name || t('common:labels.unknown')}
                </span>
                {run.current_user_is_leader && run.state !== 'completed' && run.state !== 'cancelled' && run.participants.length > 1 && (
                  <>
                    <button
                      onClick={() => setShowReassignPopup(true)}
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                      disabled={reassignmentRequest !== null}
                      title={reassignmentRequest ? t('run:labels.reassignmentRequestPending') : t('run:actions.reassignLeadership')}
                    >
                      {reassignmentRequest ? t('run:labels.pending') : t('run:actions.reassign')}
                    </button>
                    {run.state === 'active' && (
                      <button
                        onClick={() => setShowForceConfirmPopup(true)}
                        className="btn btn-ghost btn-sm"
                        style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                        title={t('run:actions.forceConfirmTooltip')}
                      >
                        {t('run:actions.forceConfirm')}
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
            <div className="info-item">
              <label>{t('run:labels.helpers')}:</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>{run.helpers.length > 0 ? run.helpers.join(', ') : t('common:labels.none')}</span>
                {run.current_user_is_leader && run.state !== 'completed' && run.state !== 'cancelled' && (
                  <button
                    onClick={() => setShowManageHelpersPopup(true)}
                    className="btn btn-ghost btn-sm"
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                    title={t('run:actions.manageHelpers')}
                  >
                    {t('run:actions.manage')}
                  </button>
                )}
              </div>
            </div>
            {run.comment && (
              <div className="info-item" style={{ gridColumn: '1 / -1' }}>
                <label>{t('run:labels.comment')}:</label>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                  <span style={{ flex: 1 }}>{run.comment}</span>
                  {run.current_user_is_leader && run.state !== 'completed' && run.state !== 'cancelled' && (
                    <button
                      onClick={() => setShowEditCommentPopup(true)}
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                      title={t('run:actions.editComment')}
                    >
                      {t('run:actions.edit')}
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
                  {t('run:actions.addComment')}
                </button>
              </div>
            )}
            <div className="info-item">
              <label>{t('run:labels.status')}:</label>
              <span>{stateDisplay.description}</span>
            </div>
          </div>
        </div>

        {/* Total Run Price Summary */}
        {runPriceSummary && run.state !== 'cancelled' && (
          <div className="info-card" style={{ marginTop: '1rem' }}>
            <h3>{t('run:labels.totalRunPrice')}</h3>
            {runPriceSummary.type === 'estimated' && (
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--color-primary)' }}>
                {runPriceSummary.total.toFixed(2)} RSD
                <span style={{ fontSize: '0.875rem', fontWeight: 'normal', color: 'var(--color-text-secondary)', marginLeft: '0.5rem' }}>
                  ({t('run:labels.estimated')})
                </span>
              </div>
            )}
            {runPriceSummary.type === 'split' && (
              <div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                    {t('run:labels.purchased')}: <strong style={{ color: 'var(--color-success)' }}>{runPriceSummary.purchased.toFixed(2)} RSD</strong>
                  </div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                    {t('run:labels.remainingEstimate')}: <strong>{runPriceSummary.remaining.toFixed(2)} RSD</strong>
                  </div>
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--color-primary)', paddingTop: '0.5rem', borderTop: '1px solid var(--color-border)' }}>
                  {runPriceSummary.total.toFixed(2)} RSD
                </div>
              </div>
            )}
            {runPriceSummary.type === 'final' && (
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--color-success)' }}>
                {runPriceSummary.total.toFixed(2)} RSD
              </div>
            )}
          </div>
        )}

        {run.state === 'active' && (
          <ErrorBoundary>
            <div className="info-card">
              <h3>{t('run:labels.participants')}</h3>
              <div className="participants-list">
                {run.participants.map(participant => (
                  <div key={participant.user_id} className="participant-item">
                    <div className="participant-info">
                      <span className={`participant-name ${participant.is_removed ? 'removed-user' : ''}`}>
                        {participant.user_name}
                        {participant.is_leader && <span className="leader-badge">{t('run:labels.leader')}</span>}
                        {participant.is_helper && <span className="helper-badge">{t('run:labels.helper')}</span>}
                      </span>
                    </div>
                    <div className="participant-ready">
                      {participant.is_ready ? (
                        <span className="ready-indicator ready">{t('run:labels.ready')}</span>
                      ) : (
                        <span className="ready-indicator not-ready">{t('run:labels.notReady')}</span>
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
                    {toggleReadyMutation.isPending ? t('run:labels.updating') : t('run:labels.imReady')}
                  </span>
                </label>
                <p className="ready-hint">{t('run:labels.readyHint')}</p>
              </div>
            </div>
          </ErrorBoundary>
        )}

        {run.state === 'confirmed' && run.current_user_is_leader && (
          <div className="info-card">
            <h3>{t('run:labels.readyToShop')}</h3>
            <p>{t('run:labels.allParticipantsReady')}</p>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                onClick={handleStartShopping}
                className="btn btn-primary btn-lg"
                disabled={startShoppingMutation.isPending}
              >
                {startShoppingMutation.isPending ? t('run:labels.starting') : t('run:actions.startShopping')}
              </button>
              <DownloadRunStateButton
                runId={runId}
                storeName={run.store_name}
                className="btn btn-secondary btn-lg"
              />
            </div>
            <p className="ready-hint">
              {t('run:labels.startShoppingHint')}
            </p>
          </div>
        )}

        {run.state === 'shopping' && (run.current_user_is_leader || run.current_user_is_helper) && (
          <div className="info-card">
            <h3>{t('run:labels.shoppingInProgress')}</h3>
            <p>{t('run:labels.currentlyShopping')}</p>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => navigate(`/shopping/${runId}`)}
                className="btn btn-success btn-lg"
              >
                {t('run:actions.openShoppingList')}
              </button>
              <DownloadRunStateButton
                runId={runId}
                storeName={run.store_name}
                className="btn btn-secondary btn-lg"
              />
            </div>
            <p className="ready-hint">
              {t('run:labels.trackPricesHint')}
            </p>
          </div>
        )}

        {run.state === 'adjusting' && run.current_user_is_leader && (
          <div className="info-card">
            <h3>{t('run:labels.adjustingBids')}</h3>
            <p>{t('run:labels.adjustingBidsDescription')}</p>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                onClick={handleFinishAdjusting}
                className="btn btn-primary btn-lg"
                disabled={finishAdjustingMutation.isPending}
              >
                {finishAdjustingMutation.isPending ? t('run:labels.processing') : t('run:actions.finishAdjusting')}
              </button>
              <button
                onClick={handleForceFinishAdjusting}
                className="btn btn-secondary btn-lg"
                disabled={finishAdjustingMutation.isPending}
              >
                {t('run:actions.forceFinish')}
              </button>
              <DownloadRunStateButton
                runId={runId}
                storeName={run.store_name}
                className="btn btn-secondary btn-lg"
              />
            </div>
            <p className="ready-hint">
              {t('run:labels.finishAdjustingHint')}
            </p>
          </div>
        )}

      </div>

      {/* User Breakdown Section - shown in all states except cancelled */}
      {run && run.state !== 'cancelled' && (
        <div className="distribution-section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3>
              {shouldFetchDistribution
                ? t('run:labels.distribution')
                : t('run:labels.userBreakdown')}
              {!shouldFetchDistribution && (
                <span style={{ fontSize: '0.8em', color: 'var(--color-text-secondary)', marginLeft: '0.5rem' }}>
                  ({t('run:labels.estimated')})
                </span>
              )}
            </h3>
            {shouldFetchDistribution && (run.current_user_is_leader || run.current_user_is_helper) && (
              <DownloadRunStateButton
                runId={runId}
                storeName={run.store_name}
                className="btn btn-secondary"
              />
            )}
          </div>

          {shouldFetchDistribution ? (
            <>
              {/* Distribution state: show actual distribution data */}
              {distributionUsers.length === 0 ? (
                <div className="empty-state">
                  <p>{t('run:empty.noItemsToDistribute')}</p>
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
                    {user.all_picked_up && <span className="pickup-badge">{t('run:labels.pickedUp')}</span>}
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
                          {markPickedUpMutation.isPending ? t('run:labels.updating') : t('run:actions.markAllPickedUp')}
                        </button>
                      )}
                    </div>
                    {user.products
                      .sort((a, b) => {
                        // Sort unpicked items first
                        if (!a.is_picked_up && b.is_picked_up) return -1
                        if (a.is_picked_up && !b.is_picked_up) return 1
                        return 0
                      })
                      .map(product => (
                      <div key={product.bid_id} className={`product-item ${product.is_picked_up ? 'picked-up' : ''}`}>
                        <div className="product-info">
                          <div className="product-name">
                            {product.product_name}
                            {product.distributed_quantity < product.requested_quantity && (
                              <span className="shortage-badge" title={t('run:labels.quantityReducedTooltip')}>⚠️</span>
                            )}
                          </div>
                          <div className="product-details">
                            <span>{t('run:labels.requested')}: {product.requested_quantity}{product.product_unit ? ` ${product.product_unit}` : ''}</span>
                            <span>{t('run:labels.allocated')}: {product.distributed_quantity}{product.product_unit ? ` ${product.product_unit}` : ''} <span className="remaining-info">({product.remaining_total}/{product.distributed_total} {t('run:labels.left')})</span></span>
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
                            {markPickedUpMutation.isPending ? t('run:labels.updating') : product.is_picked_up ? t('run:labels.pickedUp') : t('run:actions.markPickedUp')}
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
                    {completeDistributionMutation.isPending ? t('run:labels.completing') : t('run:actions.completeRun')}
                  </button>
                </div>
              )}
            </>
          ) : (
            // Pre-distribution states: show breakdown from bids
            userBreakdownFromBids.length === 0 ? (
              <div className="empty-state">
                <p>{t('run:empty.noBidsYet')}</p>
              </div>
            ) : (
              <div className="distribution-list">
                {userBreakdownFromBids.map(user => (
                  <div key={user.user_id} className="user-card">
                    <div
                      className="user-header"
                      onClick={() => toggleExpand(user.user_id)}
                    >
                      <div className="user-info">
                        <span className="user-name">{user.user_name}</span>
                        <span className="user-total">{user.total_cost} RSD</span>
                      </div>
                      <div className="user-actions">
                        <span className="expand-icon">{expandedUserId === user.user_id ? '▼' : '▶'}</span>
                      </div>
                    </div>

                    {expandedUserId === user.user_id && (
                      <div className="user-products">
                        {user.products.map(product => (
                          <div key={product.product_id} className="product-item">
                            <div className="product-info">
                              <div className="product-name">
                                {product.product_name}
                              </div>
                              <div className="product-details">
                                <span>{t('run:labels.quantity')}: {product.quantity}{product.product_unit ? ` ${product.product_unit}` : ''}</span>
                                {product.price_per_unit > 0 && (
                                  <>
                                    <span>@{product.price_per_unit} RSD</span>
                                    <span className="product-subtotal">{product.subtotal.toFixed(2)} RSD</span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      )}

      <div className="products-section">
        <div className="products-header">
          <h3>{t('run:labels.products', { count: run.products.length })}</h3>
          {canBid && run.state !== 'adjusting' && (
            <button onClick={handleAddProduct} className="add-product-button">
              {t('run:actions.addProduct')}
            </button>
          )}
        </div>

        {run.products.length === 0 ? (
          <div className="no-products">
            <p>{t('run:empty.noProducts')}</p>
          </div>
        ) : (
          <div className="products-list">
            {run.products
              .sort((a, b) => {
                // In adjusting state, sort by adjustment status
                if (run.state === 'adjusting') {
                  const aNeedsAdjustment = a.purchased_quantity !== null &&
                                          a.purchased_quantity > 0 &&
                                          a.total_quantity !== a.purchased_quantity
                  const bNeedsAdjustment = b.purchased_quantity !== null &&
                                          b.purchased_quantity > 0 &&
                                          b.total_quantity !== b.purchased_quantity

                  // Products needing adjustment (shortage or surplus) come first
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
            <p>{t('run:states.activeDescription')}</p>
          </div>
        </div>
      )}

      {run.state === 'planning' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>{t('run:states.planningDescription')}</p>
          </div>
        </div>
      )}

      {run.state === 'confirmed' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>{t('run:states.confirmedDescription')}</p>
          </div>
        </div>
      )}

      {run.state === 'shopping' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>{t('run:states.shoppingDescription')}</p>
          </div>
        </div>
      )}

      {run.state === 'adjusting' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>{t('run:states.adjustingDescription')}</p>
          </div>
        </div>
      )}

      {run.state === 'completed' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>{t('run:states.completedDescription')}</p>
          </div>
        </div>
      )}

      <Suspense fallback={null}>
        {showBidPopup && selectedProduct && (() => {
          const isAdjustingMode = run?.state === 'adjusting'
          const currentBid = selectedProduct.current_user_bid
          const hasPurchasedQuantity = selectedProduct.purchased_quantity !== null

          // Calculate difference: positive = surplus, negative = shortage
          const difference = hasPurchasedQuantity && selectedProduct.purchased_quantity !== null
            ? selectedProduct.purchased_quantity - selectedProduct.total_quantity
            : 0

          let minAllowed: number | undefined = undefined
          let maxAllowed: number | undefined = undefined

          if (isAdjustingMode && currentBid && hasPurchasedQuantity) {
            if (difference < 0) {
              // Shortage: can only decrease, but not below (currentBid - shortage)
              const shortage = Math.abs(difference)
              minAllowed = Math.max(0, currentBid.quantity - shortage)
              maxAllowed = currentBid.quantity
            } else if (difference > 0) {
              // Surplus: can only increase, but not above (currentBid + surplus)
              const surplus = difference
              minAllowed = currentBid.quantity
              maxAllowed = currentBid.quantity + surplus
            } else {
              // No difference, quantities match (shouldn't happen in adjusting mode)
              minAllowed = currentBid.quantity
              maxAllowed = currentBid.quantity
            }
          }

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

        {showCommentsPopup && selectedProduct && run && (
          <CommentsPopup
            productName={selectedProduct.name}
            userBids={selectedProduct.user_bids}
            currentUserId={userId}
            canEdit={run.state === 'planning' || run.state === 'active' || run.state === 'adjusting'}
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
              showToast(t('run:messages.reassignmentRequestSent'), 'success')
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
              showToast(t('run:messages.runForceConfirmed'), 'success')
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
            showToast(t('run:messages.commentUpdated'), 'success')
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
  const { t } = useTranslation(['common', 'run'])
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
      setError(getErrorMessage(err, 'Failed to update comment'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-sm" onClick={e => e.stopPropagation()}>
        <h3>{t('run:actions.editComment')}</h3>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="comment" className="form-label">{t('run:labels.comment')}</label>
            <textarea
              id="comment"
              className="form-input"
              value={comment}
              onChange={e => setComment(e.target.value)}
              placeholder={t('run:labels.commentPlaceholder')}
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
              {t('common:actions.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? t('common:actions.saving') : t('common:actions.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}