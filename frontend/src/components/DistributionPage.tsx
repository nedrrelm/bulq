import { useState, useEffect } from 'react'
import './DistributionPage.css'
import { API_BASE_URL } from '../config'
import LoadingSpinner from './LoadingSpinner'
import './LoadingSpinner.css'
import ErrorAlert from './ErrorAlert'

interface DistributionProduct {
  bid_id: string
  product_id: string
  product_name: string
  requested_quantity: number
  distributed_quantity: number
  price_per_unit: string
  subtotal: string
  is_picked_up: boolean
}

interface DistributionUser {
  user_id: string
  user_name: string
  products: DistributionProduct[]
  total_cost: string
  all_picked_up: boolean
}

interface DistributionPageProps {
  runId: string
  onBack: () => void
}

export default function DistributionPage({ runId, onBack }: DistributionPageProps) {
  const [users, setUsers] = useState<DistributionUser[]>([])
  const [expandedUserId, setExpandedUserId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDistributionData = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_BASE_URL}/distribution/${runId}`, {
        credentials: 'include'
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to load distribution data: ${response.status} - ${errorText}`)
      }

      const data = await response.json()
      setUsers(data)
    } catch (err) {
      console.error('Distribution page error:', err)
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDistributionData()
  }, [runId])

  const handlePickup = async (bidId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/distribution/${runId}/pickup/${bidId}`, {
        method: 'POST',
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Failed to mark as picked up')
      }

      // Reload data after successful pickup
      await loadDistributionData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
  }

  const handleMarkAllPickedUp = async (user: DistributionUser) => {
    try {
      // Mark all unpicked products for this user as picked up
      const unpickedProducts = user.products.filter(p => !p.is_picked_up)

      for (const product of unpickedProducts) {
        const response = await fetch(`${API_BASE_URL}/distribution/${runId}/pickup/${product.bid_id}`, {
          method: 'POST',
          credentials: 'include'
        })

        if (!response.ok) {
          throw new Error('Failed to mark as picked up')
        }
      }

      // Reload data after successful pickup
      await loadDistributionData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
  }

  const handleCompleteRun = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/distribution/${runId}/complete`, {
        method: 'POST',
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Failed to complete run')
      }

      // Go back to run page after completion
      onBack()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    }
  }

  const toggleExpand = (userId: string) => {
    setExpandedUserId(expandedUserId === userId ? null : userId)
  }

  const allPickedUp = users.length > 0 && users.every(user => user.all_picked_up)

  if (loading) {
    return <LoadingSpinner />
  }

  if (error) {
    return <ErrorAlert message={error} onRetry={loadDistributionData} />
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
                    >
                      Mark All Picked Up
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
                      disabled={product.is_picked_up}
                      className={`pickup-button ${product.is_picked_up ? 'picked-up' : ''}`}
                    >
                      {product.is_picked_up ? '✓ Picked up' : 'Mark Picked Up'}
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
          <button onClick={handleCompleteRun} className="complete-button">
            Complete Run
          </button>
        </div>
      )}
    </div>
  )
}
