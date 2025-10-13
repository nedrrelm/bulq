import { useState, useMemo } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import '../styles/components/DistributionPage.css'
import LoadingSpinner from './LoadingSpinner'
import '../styles/components/LoadingSpinner.css'
import ErrorAlert from './ErrorAlert'
import { useDistribution, useMarkPickedUp, useCompleteDistribution } from '../hooks/queries/useDistribution'
import type { DistributionUser } from '../schemas/distribution'
import { logger } from '../utils/logger'

export default function DistributionPage() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()

  // Redirect if no runId
  if (!runId) {
    navigate('/')
    return null
  }
  const [expandedUserId, setExpandedUserId] = useState<string | null>(null)

  // Use React Query hooks
  const { data: allUsers = [], isLoading, error: queryError, refetch } = useDistribution(runId)
  const markPickedUpMutation = useMarkPickedUp(runId)
  const completeDistributionMutation = useCompleteDistribution(runId)

  // Filter out users who have no purchased products
  const users = useMemo(() => {
    return allUsers
      .map((user) => ({
        ...user,
        products: user.products.filter(p => p.distributed_quantity > 0)
      }))
      .filter((user) => user.products.length > 0)
  }, [allUsers])

  // Convert React Query error to string
  const error = queryError instanceof Error ? queryError.message : null

  const handlePickup = async (bidId: string) => {
    try {
      await markPickedUpMutation.mutateAsync(bidId)
    } catch (err) {
      logger.error('Failed to mark as picked up:', err)
    }
  }

  const handleMarkAllPickedUp = async (user: DistributionUser) => {
    try {
      // Mark all unpicked products for this user as picked up
      const unpickedProducts = user.products.filter(p => !p.is_picked_up)

      for (const product of unpickedProducts) {
        await markPickedUpMutation.mutateAsync(product.bid_id)
      }
    } catch (err) {
      logger.error('Failed to mark all as picked up:', err)
    }
  }

  const handleCompleteRun = async () => {
    try {
      await completeDistributionMutation.mutateAsync()
      // Go back to run page after completion
      navigate(`/runs/${runId}`)
    } catch (err) {
      logger.error('Failed to complete run:', err)
    }
  }

  const toggleExpand = (userId: string) => {
    setExpandedUserId(expandedUserId === userId ? null : userId)
  }

  const allPickedUp = users.length > 0 && users.every(user => user.all_picked_up)

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (error) {
    return <ErrorAlert message={error} onRetry={() => refetch()} />
  }

  return (
    <div className="distribution-page">
      <div className="page-header">
        <button onClick={onBack} className="back-button">← Back to Run</button>
        <h2>Distribution</h2>
      </div>

      <div className="distribution-list">
        {users.map(user => (
          <div key={user.user_id} className={`user-card ${user.all_picked_up ? 'completed' : ''}`}>
            <div
              className="user-header"
              onClick={() => toggleExpand(user.user_id)}
            >
              <div className="user-info">
                <span className="user-name">{user.user_name}</span>
                <span className="user-total">${user.total_cost}</span>
              </div>
              <div className="user-actions">
                {user.all_picked_up && <span className="pickup-badge">✓ Picked up</span>}
                <span className="expand-icon">{expandedUserId === user.user_id ? '▼' : '▶'}</span>
              </div>
            </div>

            {expandedUserId === user.user_id && (
              <div className="user-products">
                <div className="user-products-header">
                  {!user.all_picked_up && (
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
                      <div className="product-name">{product.product_name}</div>
                      <div className="product-details">
                        <span>Requested: {product.requested_quantity}</span>
                        <span>Distributed: {product.distributed_quantity}</span>
                        <span>@${product.price_per_unit}</span>
                        <span className="product-subtotal">${product.subtotal}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handlePickup(product.bid_id)}
                      disabled={product.is_picked_up || markPickedUpMutation.isPending}
                      className={`pickup-button ${product.is_picked_up ? 'picked-up' : ''}`}
                    >
                      {markPickedUpMutation.isPending ? '⏳ Updating...' : product.is_picked_up ? '✓ Picked up' : 'Mark Picked Up'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {users.length === 0 && (
          <div className="empty-state">No distribution data available</div>
        )}
      </div>

      {allPickedUp && (
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
  )
}
