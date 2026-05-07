import { useState, useEffect, useCallback, lazy, Suspense, useMemo } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import '../styles/pages/RunPage.css'
import '../styles/run-states.css'
import { WS_BASE_URL } from '../config'
import { runsApi, reassignmentApi, shoppingApi } from '../api'
import type { RunDetail } from '../api'
import type { AvailableProduct, LeaderReassignmentRequest } from '../types'
import type { WebSocketMessage } from '../types/websocket'
import { shoppingKeys } from '../hooks/queries'
import ErrorBoundary from '../components/common/ErrorBoundary'
import { getErrorMessage } from '../utils/errorHandling'

// Lazy load popup components for better code splitting
const BidPopup = lazy(() => import('../components/popups/BidPopup'))
const AddProductPopup = lazy(() => import('../components/popups/AddProductPopup'))
const ReassignLeaderPopup = lazy(() => import('../components/popups/ReassignLeaderPopup'))
const ManageHelpersPopup = lazy(() => import('../components/popups/ManageHelpersPopup'))
const ForceConfirmPopup = lazy(() => import('../components/popups/ForceConfirmPopup'))
const CommentsPopup = lazy(() => import('../components/popups/CommentsPopup'))
const EditCommentPopup = lazy(() => import('../components/popups/EditCommentPopup'))
import RunProductItem from '../components/RunProductItem'
import RunActionCards from '../components/RunActionCards'
import RunDistributionSection from '../components/RunDistributionSection'
import { useWebSocket } from '../hooks/useWebSocket'
import { getStateDisplay } from '../utils/runStates'
import Toast from '../components/common/Toast'
import ConfirmDialog from '../components/common/ConfirmDialog'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { useNotifications } from '../hooks/useNotifications'
import { useRun, runKeys, useToggleReady, useRevertToActive, useStartShopping, useFinishAdjusting } from '../hooks/queries'
import { useAuth } from '../hooks/useAuth'
import { handleError, formatErrorForDisplay } from '../utils/errorHandling'
import { useDistribution, useMarkPickedUp, useCompleteDistribution, useCreateGroup, useDeleteGroup, useAssignUserToGroup, useMarkGroupDone, distributionKeys } from '../hooks/queries/useDistribution'
import type { DistributionUser } from '../schemas/distribution'

// Using RunDetail type from API layer
type Product = RunDetail['products'][0]

export default function RunPage() {
  const { t } = useTranslation(['common', 'run'])
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()

  // Use React Query for run data
  const { data: run, isLoading: loading, error: queryError } = useRun(runId || '')
  const queryClient = useQueryClient()
  const toggleReadyMutation = useToggleReady(runId || '')
  const revertToActiveMutation = useRevertToActive(runId || '')
  const startShoppingMutation = useStartShopping(runId || '')
  const finishAdjustingMutation = useFinishAdjusting(runId || '')

  // Distribution data (only fetched when in distributing or completed state)
  const shouldFetchDistribution = run?.state === 'distributing' || run?.state === 'completed'
  const { data: distributionData } = useDistribution(runId || '', { enabled: shouldFetchDistribution })
  const markPickedUpMutation = useMarkPickedUp(runId || '')
  const completeDistributionMutation = useCompleteDistribution(runId || '')
  const createGroupMutation = useCreateGroup(runId || '')
  const deleteGroupMutation = useDeleteGroup(runId || '')
  const assignUserToGroupMutation = useAssignUserToGroup(runId || '')
  const markGroupDoneMutation = useMarkGroupDone(runId || '')
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
  const [leaderEditMode, setLeaderEditMode] = useState(false)
  const [leaderEditTimer, setLeaderEditTimer] = useState<ReturnType<typeof setTimeout> | null>(null)
  const [selectedTargetUser, setSelectedTargetUser] = useState<{ userId: string, userName: string } | null>(null)
  const [reassignmentRequest, setReassignmentRequest] = useState<LeaderReassignmentRequest | null>(null)
  const { toast, showToast, hideToast } = useToast()
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()
  const { refreshUnreadCount } = useNotifications()

  const userId = user?.id

  const fetchReassignmentRequest = useCallback(async () => {
    if (!runId) return
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
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
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
  }, [run, userId, showToast, fetchReassignmentRequest, queryClient, runId, refreshUnreadCount, t])

  useWebSocket(
    runId ? `${WS_BASE_URL}/ws/runs/${runId}` : null,
    {
      onMessage: handleWebSocketMessage
    }
  )

  const canBid = run?.state === 'planning' || run?.state === 'active' || run?.state === 'adjusting'

  useEffect(() => {
    return () => {
      if (leaderEditTimer) clearTimeout(leaderEditTimer)
    }
  }, [leaderEditTimer])

  const handleToggleLeaderEditMode = () => {
    if (leaderEditMode) {
      setLeaderEditMode(false)
      if (leaderEditTimer) {
        clearTimeout(leaderEditTimer)
        setLeaderEditTimer(null)
      }
    } else {
      setLeaderEditMode(true)
      const timer = setTimeout(() => {
        setLeaderEditMode(false)
        setLeaderEditTimer(null)
      }, 5 * 60 * 1000)
      setLeaderEditTimer(timer)
    }
  }

  const handleEditUserBid = (product: Product, userId: string, userName: string) => {
    setSelectedProduct(product)
    setSelectedTargetUser({ userId, userName })
    setShowBidPopup(true)
  }

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

    if (selectedTargetUser) {
      try {
        await runsApi.leaderEditBid(runId, {
          product_id: selectedProduct.id,
          user_id: selectedTargetUser.userId,
          quantity,
          interested_only: interestedOnly,
          comment
        })
        setShowBidPopup(false)
        setSelectedProduct(null)
        setSelectedTargetUser(null)
      } catch (err) {
        showToast(formatErrorForDisplay(err, 'edit user bid'), 'error')
      }
      return
    }

    try {
      // If in shopping state, add to shopping list; otherwise place a regular bid
      if (run?.state === 'shopping') {
        await shoppingApi.addProductToShoppingList(runId, selectedProduct.id, quantity)
        // Invalidate shopping list and run details to refetch
        queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
        queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
        showToast(t('shopping:messages.productAdded'), 'success')
      } else {
        await runsApi.placeBid(runId, {
          product_id: selectedProduct.id,
          quantity,
          interested_only: interestedOnly,
          comment
        })
        // WebSocket will update the run data automatically
      }

      setShowBidPopup(false)
      setSelectedProduct(null)
    } catch (err) {
      showToast(formatErrorForDisplay(err, run?.state === 'shopping' ? 'add product to shopping list' : 'place bid'), 'error')
    }
  }

  const handleCancelBid = () => {
    setShowBidPopup(false)
    setSelectedProduct(null)
    setSelectedTargetUser(null)
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

  const handleProductSelected = (product: AvailableProduct) => {
    setShowAddProductPopup(false)

    // Convert available product to full product format
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

  const handleRevertToActive = () => {
    showConfirm(
      t('run:prompts.revertToActive'),
      async () => {
        try {
          await revertToActiveMutation.mutateAsync()
          showToast(t('run:messages.revertedToActive'), 'success')
        } catch (err) {
          showToast(formatErrorForDisplay(err, 'revert to active'), 'error')
        }
      }
    )
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

  const handleCreateGroup = async () => {
    try {
      await createGroupMutation.mutateAsync()
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'create group'), 'error')
    }
  }

  const handleDeleteGroup = async (groupId: string) => {
    try {
      await deleteGroupMutation.mutateAsync(groupId)
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'delete group'), 'error')
    }
  }

  const handleAssignUserToGroup = async (groupId: string, userId: string) => {
    try {
      await assignUserToGroupMutation.mutateAsync({ groupId, userId })
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'assign user to group'), 'error')
    }
  }

  const handleMarkGroupDone = async (groupId: string) => {
    try {
      await markGroupDoneMutation.mutateAsync(groupId)
    } catch (err) {
      showToast(formatErrorForDisplay(err, 'mark group as done'), 'error')
    }
  }

  const toggleExpand = (userId: string) => {
    setExpandedUserId(expandedUserId === userId ? null : userId)
  }

  // Enrich distribution groups with per-group product totals
  const distributionGroups = useMemo(() => {
    if (!distributionData) return []

    return distributionData.groups.map(group => {
      // Calculate product totals within this group only
      const groupProductTotals = new Map<string, { total: number, remaining: number }>()

      group.users.forEach(user => {
        user.products.forEach(product => {
          if (product.distributed_quantity && product.distributed_quantity > 0) {
            const existing = groupProductTotals.get(product.product_id) || { total: 0, remaining: 0 }
            existing.total += product.distributed_quantity
            if (!product.is_picked_up) {
              existing.remaining += product.distributed_quantity
            }
            groupProductTotals.set(product.product_id, existing)
          }
        })
      })

      const enrichedUsers = group.users
        .map(user => {
          const filteredProducts = user.products.filter(p =>
            p.distributed_quantity && p.distributed_quantity > 0
          )
          const enrichedProducts = filteredProducts.map(p => {
            const totals = groupProductTotals.get(p.product_id)
            return {
              ...p,
              remaining_total: totals?.remaining || 0,
              distributed_total: totals?.total || 0
            }
          })
          return { ...user, products: enrichedProducts }
        })
        .filter(user => user.products.length > 0)

      return { ...group, users: enrichedUsers }
    })
  }, [distributionData])

  // Flatten all users across groups for backward-compatible checks
  const distributionUsers = useMemo(() => {
    return distributionGroups.flatMap(g => g.users)
  }, [distributionGroups])

  const allPickedUp = distributionUsers.length > 0 && distributionUsers.every(user => user.all_picked_up)
  const isLeaderOrHelper = run?.current_user_is_leader || run?.current_user_is_helper

  // Calculate user breakdown from bids for pre-distribution states
  const userBreakdownFromBids = useMemo(() => {
    if (!run || shouldFetchDistribution) return []

    const leaderFee = run.leader_fee ? parseFloat(run.leader_fee) : 0

    // Determine fee-exempt participants (leader + helpers)
    const exemptUserIds = new Set(
      run.participants
        .filter(p => p.is_leader || p.is_helper)
        .map(p => p.user_id)
    )

    const breakdown = run.participants
      .map(participant => {
        const userProducts = run.products
          .filter(product => {
            // In adjusting state, only include products that were purchased
            if (run.state === 'adjusting') {
              return product.purchased_quantity !== null && product.purchased_quantity > 0
            }
            return true
          })
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
          is_leader: participant.is_leader,
          is_helper: participant.is_helper,
          products: userProducts,
          total_cost: totalCost.toFixed(2),
          fee_share: '0.00'
        }
      })
      .filter(user => user.products.length > 0)

    // Calculate fee share for non-exempt participants
    if (leaderFee > 0) {
      const feePayingUsers = breakdown.filter(u => !exemptUserIds.has(u.user_id))
      if (feePayingUsers.length > 0) {
        const feeShare = leaderFee / feePayingUsers.length
        for (const user of feePayingUsers) {
          user.fee_share = feeShare.toFixed(2)
          user.total_cost = (parseFloat(user.total_cost) + feeShare).toFixed(2)
        }
      }
    }

    return breakdown
  }, [run, shouldFetchDistribution])

  // Calculate total run price based on state
  const runPriceSummary = useMemo(() => {
    if (!run) return null

    const leaderFee = run.leader_fee ? parseFloat(run.leader_fee) : 0

    if (shouldFetchDistribution && distributionUsers.length > 0) {
      // Distributing/Completed: Use actual distribution data (fee already included in total_cost)
      const finalTotal = distributionUsers.reduce((sum, user) => {
        return sum + parseFloat(user.total_cost)
      }, 0)
      return {
        type: 'final' as const,
        total: finalTotal,
        leaderFee
      }
    }

    if (run.state === 'adjusting') {
      // Adjusting: Show purchased + remaining estimate
      let purchasedTotal = 0
      const remainingEstimate = 0

      run.products.forEach(product => {
        const price = product.current_price ? parseFloat(product.current_price) : 0

        if (product.purchased_quantity !== null && product.purchased_quantity !== undefined && product.purchased_quantity > 0) {
          purchasedTotal += price * product.purchased_quantity
        }
      })

      return {
        type: 'split' as const,
        purchased: purchasedTotal,
        remaining: remainingEstimate,
        total: purchasedTotal + remainingEstimate + leaderFee,
        leaderFee
      }
    }

    // Pre-shopping (planning, active, confirmed, shopping): Estimated total
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
      total: estimatedTotal + leaderFee,
      leaderFee
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

  // Redirect if no runId or user
  if (!runId || !user) {
    navigate('/')
    return null
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

      {/* Sale context banner */}
      {run.sale_id && (
        <div className="sale-context-banner">
          <span className="sale-context-label">{t('run:sale.fromSale')}</span>
          <strong>{run.sale_title}</strong>
          {run.seller_name && <span className="sale-context-seller"> — {run.seller_name}</span>}
        </div>
      )}

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
              <div className="flex-center-gap-sm">
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
              <div className="flex-center-gap-sm">
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
                <div className="flex-start-gap-sm">
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
              <label>{t('run:labels.leaderFee')}:</label>
              <div className="flex-center-gap-sm">
                <span style={{ fontWeight: run.leader_fee ? 'bold' : 'normal', color: run.leader_fee ? 'var(--color-primary)' : undefined }}>
                  {run.leader_fee ? `${run.leader_fee} RSD` : t('run:labels.noFee')}
                </span>
                {run.current_user_is_leader && run.state === 'planning' && (
                  <button
                    onClick={() => {
                      const newFee = prompt(t('run:fields.leaderFee'), run.leader_fee || '0')
                      if (newFee !== null) {
                        const feeNum = parseFloat(newFee)
                        if (!isNaN(feeNum) && feeNum >= 0) {
                          runsApi.updateLeaderFee(runId, { leader_fee: feeNum || null }).then(() => {
                            showToast(t('run:messages.leaderFeeUpdated'), 'success')
                            queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
                          }).catch((err: unknown) => {
                            showToast(formatErrorForDisplay(err, 'update leader fee'), 'error')
                          })
                        }
                      }
                    }}
                    className="btn btn-ghost btn-sm"
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                  >
                    {t('run:actions.edit')}
                  </button>
                )}
              </div>
            </div>
            <div className="info-item">
              <label>{t('run:labels.status')}:</label>
              <span>{stateDisplay.description}</span>
            </div>
          </div>
        </div>

        {/* Total Run Price Summary */}
        {runPriceSummary && run.state !== 'cancelled' && (
          <div className="info-card" className="mt-md">
            <h3>{t('run:labels.totalRunPrice')}</h3>
            {runPriceSummary.type === 'estimated' && (
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--color-primary)' }}>
                {runPriceSummary.total.toFixed(2)} RSD
                <span className="text-sm font-normal text-secondary ml-sm">
                  ({t('run:labels.estimated')})
                </span>
              </div>
            )}
            {runPriceSummary.type === 'split' && (
              <div>
                <div className="mb-sm">
                  <div className="text-sm text-secondary">
                    {t('run:labels.purchased')}: <strong style={{ color: 'var(--color-success)' }}>{runPriceSummary.purchased.toFixed(2)} RSD</strong>
                  </div>
                  <div className="text-sm text-secondary">
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

        <RunActionCards
          run={run}
          runId={runId}
          onToggleReady={handleToggleReady}
          toggleReadyPending={toggleReadyMutation.isPending}
          onRevertToActive={handleRevertToActive}
          revertToActivePending={revertToActiveMutation.isPending}
          onStartShopping={handleStartShopping}
          startShoppingPending={startShoppingMutation.isPending}
          onFinishAdjusting={handleFinishAdjusting}
          onForceFinishAdjusting={handleForceFinishAdjusting}
          finishAdjustingPending={finishAdjustingMutation.isPending}
          onShowForceConfirmPopup={() => setShowForceConfirmPopup(true)}
          onNavigateToShopping={() => navigate(`/shopping/${runId}`)}
        />

      </div>

      {/* User Breakdown Section */}
      {run.state !== 'cancelled' && (
        <RunDistributionSection
          run={run}
          runId={runId}
          shouldFetchDistribution={shouldFetchDistribution}
          distributionGroups={distributionGroups}
          distributionUsers={distributionUsers}
          userBreakdownFromBids={userBreakdownFromBids}
          expandedUserId={expandedUserId}
          onToggleExpand={toggleExpand}
          allPickedUp={allPickedUp}
          isLeaderOrHelper={isLeaderOrHelper || false}
          onMarkPickedUp={handlePickup}
          onMarkAllPickedUp={handleMarkAllPickedUp}
          onCompleteRun={handleCompleteRun}
          onCreateGroup={handleCreateGroup}
          onDeleteGroup={handleDeleteGroup}
          onAssignUserToGroup={handleAssignUserToGroup}
          onMarkGroupDone={handleMarkGroupDone}
          markPickedUpPending={markPickedUpMutation.isPending}
          completeDistributionPending={completeDistributionMutation.isPending}
        />
      )}

      <div className="products-section">
        <div className="products-header">
          <h3>{t('run:labels.products', { count: run.products.length })}</h3>
          {run.current_user_is_leader && canBid && (
            <label className="leader-edit-toggle">
              <input
                type="checkbox"
                checked={leaderEditMode}
                onChange={handleToggleLeaderEditMode}
              />
              <span>{t('run:actions.editMemberBids')}</span>
            </label>
          )}
          {(canBid || (run.state === 'shopping' && (run.current_user_is_leader || run.helpers.includes(user?.id || '')))) && (
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
                if (run.state === 'adjusting') {
                  // Adjusting: needs adjustment → correctly bought → unbought, alphabetically
                  const getCategoryAndName = (product: Product) => {
                    const purchased = product.purchased_quantity !== null && product.purchased_quantity > 0
                    const needsAdjustment = purchased && product.total_quantity !== product.purchased_quantity

                    if (needsAdjustment) {
                      return { category: 0, name: product.name }
                    } else if (purchased) {
                      return { category: 1, name: product.name }
                    } else {
                      return { category: 2, name: product.name }
                    }
                  }

                  const aData = getCategoryAndName(a)
                  const bData = getCategoryAndName(b)

                  if (aData.category !== bData.category) {
                    return aData.category - bData.category
                  }
                  return aData.name.localeCompare(bData.name)
                } else if (run.state === 'distributing' || run.state === 'completed') {
                  // Distributing/Completed: bought → unbought, alphabetically
                  const aPurchased = a.purchased_quantity !== null && a.purchased_quantity > 0
                  const bPurchased = b.purchased_quantity !== null && b.purchased_quantity > 0

                  if (aPurchased && !bPurchased) return -1
                  if (!aPurchased && bPurchased) return 1
                  return a.name.localeCompare(b.name)
                } else {
                  // Planning, Active, Confirmed, Shopping: alphabetically
                  return a.name.localeCompare(b.name)
                }
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
                    leaderEditMode={leaderEditMode}
                    onEditUserBid={handleEditUserBid}
                  />
                </ErrorBoundary>
              ))}
          </div>
        )}
      </div>

      {['active', 'planning', 'confirmed', 'shopping', 'adjusting', 'completed'].includes(run.state) && (
        <div className="actions-section">
          <div className="info-banner">
            <p>{t(`run:states.${run.state}Description`)}</p>
          </div>
        </div>
      )}

      <Suspense fallback={null}>
        {showBidPopup && selectedProduct && (() => {
          const isAdjustingMode = run?.state === 'adjusting'
          const currentBid = selectedProduct.current_user_bid
          const targetBid = selectedTargetUser
            ? selectedProduct.user_bids.find(b => b.user_id === selectedTargetUser.userId)
            : null
          const effectiveBid = targetBid || currentBid
          const hasPurchasedQuantity = selectedProduct.purchased_quantity !== null

          // Calculate difference: positive = surplus, negative = shortage
          const difference = hasPurchasedQuantity && selectedProduct.purchased_quantity !== null
            ? selectedProduct.purchased_quantity - selectedProduct.total_quantity
            : 0

          let minAllowed: number | undefined = undefined
          let maxAllowed: number | undefined = undefined

          if (isAdjustingMode && hasPurchasedQuantity) {
            if (effectiveBid) {
              if (difference < 0) {
                // Shortage: can only decrease, but not below (effectiveBid - shortage)
                const shortage = Math.abs(difference)
                minAllowed = Math.round(Math.max(0, effectiveBid.quantity - shortage) * 100) / 100
                maxAllowed = Math.round(effectiveBid.quantity * 100) / 100
              } else if (difference > 0) {
                // Surplus: can only increase, but not above (effectiveBid + surplus)
                const surplus = difference
                minAllowed = Math.round(effectiveBid.quantity * 100) / 100
                maxAllowed = Math.round((effectiveBid.quantity + surplus) * 100) / 100
              } else {
                // No difference, quantities match (shouldn't happen in adjusting mode)
                minAllowed = Math.round(effectiveBid.quantity * 100) / 100
                maxAllowed = Math.round(effectiveBid.quantity * 100) / 100
              }
            } else if (difference > 0) {
              // New bid on surplus product: can bid up to the surplus amount
              maxAllowed = Math.round(difference * 100) / 100
            }
          }

          return (
            <BidPopup
              productName={selectedProduct.name}
              currentQuantity={selectedTargetUser ? selectedProduct.user_bids.find(b => b.user_id === selectedTargetUser.userId)?.quantity : currentBid?.quantity}
              currentComment={selectedTargetUser ? selectedProduct.user_bids.find(b => b.user_id === selectedTargetUser.userId)?.comment ?? null : currentBid?.comment}
              onSubmit={handleSubmitBid}
              onCancel={handleCancelBid}
              adjustingMode={isAdjustingMode}
              minAllowed={minAllowed}
              maxAllowed={maxAllowed}
              targetUserName={selectedTargetUser?.userName}
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
