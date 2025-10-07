import { useState, useEffect } from 'react'
import './RunPage.css'
import { API_BASE_URL } from '../config'
import BidPopup from './BidPopup'
import AddProductPopup from './AddProductPopup'
import { useWebSocket } from '../hooks/useWebSocket'

interface UserBid {
  user_id: string
  user_name: string
  quantity: number
  interested_only: boolean
}

interface Product {
  id: string
  name: string
  base_price: string
  total_quantity: number
  interested_count: number
  user_bids: UserBid[]
  current_user_bid: UserBid | null
  purchased_quantity: number | null
}

interface AvailableProduct {
  id: string
  name: string
  base_price: string
}

interface Participant {
  user_id: string
  user_name: string
  is_leader: boolean
  is_ready: boolean
}

interface RunDetail {
  id: string
  group_id: string
  group_name: string
  store_id: string
  store_name: string
  state: string
  products: Product[]
  participants: Participant[]
  current_user_is_ready: boolean
  current_user_is_leader: boolean
}

interface RunPageProps {
  runId: string
  onBack: (groupId?: string) => void
  onShoppingSelect?: (runId: string) => void
  onDistributionSelect?: (runId: string) => void
}

export default function RunPage({ runId, onBack, onShoppingSelect, onDistributionSelect }: RunPageProps) {
  const [run, setRun] = useState<RunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showBidPopup, setShowBidPopup] = useState(false)
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [showAddProductPopup, setShowAddProductPopup] = useState(false)

  useEffect(() => {
    const fetchRunDetails = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${API_BASE_URL}/runs/${runId}`, {
          credentials: 'include'
        })

        if (!response.ok) {
          const errorText = await response.text()
          throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
        }

        const runData: RunDetail = await response.json()
        setRun(runData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load run details')
      } finally {
        setLoading(false)
      }
    }

    fetchRunDetails()
  }, [runId])

  // WebSocket for real-time updates
  useWebSocket(
    runId ? `ws://localhost:8000/ws/runs/${runId}` : null,
    {
      onMessage: (message) => {
        if (!run) return

        if (message.type === 'bid_updated') {
          // Update product with new bid or updated bid
          setRun(prev => {
            if (!prev) return prev
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

                  return {
                    ...p,
                    user_bids: newUserBids,
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
                  return {
                    ...p,
                    user_bids: newUserBids,
                    total_quantity: message.data.new_total,
                    interested_count: newUserBids.filter(b => b.interested_only || b.quantity > 0).length
                  }
                }
                return p
              })
            }
          })
        } else if (message.type === 'ready_toggled') {
          // Update participant ready status
          setRun(prev => {
            if (!prev) return prev
            return {
              ...prev,
              participants: prev.participants.map(p =>
                p.user_id === message.data.user_id
                  ? { ...p, is_ready: message.data.is_ready }
                  : p
              )
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
      }
    }
  )

  const canBid = run?.state === 'planning' || run?.state === 'active' || run?.state === 'adjusting'

  const handlePlaceBid = (product: Product) => {
    setSelectedProduct(product)
    setShowBidPopup(true)
  }

  const handleRetractBid = async (product: Product) => {
    try {
      const response = await fetch(`${API_BASE_URL}/runs/${runId}/bids/${product.id}`, {
        method: 'DELETE',
        credentials: 'include'
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Failed to retract bid')
      }

      // Refresh run details
      const refreshResponse = await fetch(`${API_BASE_URL}/runs/${runId}`, {
        credentials: 'include'
      })

      if (refreshResponse.ok) {
        const runData: RunDetail = await refreshResponse.json()
        setRun(runData)
      }
    } catch (err) {
      console.error('Error retracting bid:', err)
      alert(err instanceof Error ? err.message : 'Failed to retract bid. Please try again.')
    }
  }

  const handleSubmitBid = async (quantity: number, interestedOnly: boolean) => {
    if (!selectedProduct) return

    try {
      const response = await fetch(`${API_BASE_URL}/runs/${runId}/bids`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          product_id: selectedProduct.id,
          quantity: quantity,
          interested_only: interestedOnly
        })
      })

      if (!response.ok) {
        throw new Error('Failed to place bid')
      }

      // Refresh run details
      const refreshResponse = await fetch(`${API_BASE_URL}/runs/${runId}`, {
        credentials: 'include'
      })

      if (refreshResponse.ok) {
        const runData: RunDetail = await refreshResponse.json()
        setRun(runData)
      }

      setShowBidPopup(false)
      setSelectedProduct(null)
    } catch (err) {
      console.error('Error placing bid:', err)
      alert('Failed to place bid. Please try again.')
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
      const response = await fetch(`${API_BASE_URL}/runs/${runId}/ready`, {
        method: 'POST',
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Failed to toggle ready status')
      }

      // Refresh run details
      const refreshResponse = await fetch(`${API_BASE_URL}/runs/${runId}`, {
        credentials: 'include'
      })

      if (refreshResponse.ok) {
        const runData: RunDetail = await refreshResponse.json()
        setRun(runData)
      }
    } catch (err) {
      console.error('Error toggling ready:', err)
      alert('Failed to update ready status. Please try again.')
    }
  }

  const handleStartShopping = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/runs/${runId}/start-shopping`, {
        method: 'POST',
        credentials: 'include'
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Failed to start shopping')
      }

      // Refresh run details
      const refreshResponse = await fetch(`${API_BASE_URL}/runs/${runId}`, {
        credentials: 'include'
      })

      if (refreshResponse.ok) {
        const runData: RunDetail = await refreshResponse.json()
        setRun(runData)
      }
    } catch (err) {
      console.error('Error starting shopping:', err)
      alert('Failed to start shopping. Please try again.')
    }
  }

  const handleFinishAdjusting = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/runs/${runId}/finish-adjusting`, {
        method: 'POST',
        credentials: 'include'
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Failed to finish adjusting')
      }

      // Refresh run details
      const refreshResponse = await fetch(`${API_BASE_URL}/runs/${runId}`, {
        credentials: 'include'
      })

      if (refreshResponse.ok) {
        const runData: RunDetail = await refreshResponse.json()
        setRun(runData)
      }
    } catch (err) {
      console.error('Error finishing adjusting:', err)
      alert(err instanceof Error ? err.message : 'Failed to finish adjusting. Please try again.')
    }
  }

  const getStateDisplay = (state: string) => {
    switch (state) {
      case 'planning':
        return { label: 'Planning', color: '#fbbf24', description: 'Collecting product interest' }
      case 'active':
        return { label: 'Active', color: '#10b981', description: 'Users placing bids and quantities' }
      case 'confirmed':
        return { label: 'Confirmed', color: '#3b82f6', description: 'Shopping list finalized' }
      case 'shopping':
        return { label: 'Shopping', color: '#8b5cf6', description: 'Designated shoppers executing the run' }
      case 'adjusting':
        return { label: 'Adjusting', color: '#f59e0b', description: 'Adjusting bids due to insufficient quantities' }
      case 'distributing':
        return { label: 'Distributing', color: '#14b8a6', description: 'Items being distributed to members' }
      case 'completed':
        return { label: 'Completed', color: '#6b7280', description: 'Run finished, costs calculated' }
      case 'cancelled':
        return { label: 'Cancelled', color: '#ef4444', description: 'Run was cancelled' }
      default:
        return { label: state, color: '#6b7280', description: '' }
    }
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
        <span style={{ cursor: 'pointer', color: '#667eea' }} onClick={() => onBack(run.group_id)}>
          {run.group_name}
        </span>
        {' > '}
        <span>{run.store_name}</span>
      </div>

      <div className="run-header">
        <div className="run-title">
          <h2>{run.store_name}</h2>
          <span
            className="run-state"
            style={{
              backgroundColor: stateDisplay.color,
              color: 'white',
              padding: '6px 16px',
              borderRadius: '16px',
              fontSize: '0.875rem',
              fontWeight: 'bold'
            }}
          >
            {stateDisplay.label}
          </span>
        </div>
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
        )}

        {run.state === 'confirmed' && run.current_user_is_leader && (
          <div className="info-card">
            <h3>Ready to Shop</h3>
            <p>All participants are ready! The shopping list is finalized.</p>
            <button
              onClick={handleStartShopping}
              className="btn btn-primary btn-lg"
              style={{ marginTop: '16px', width: '100%' }}
            >
              🛒 Start Shopping
            </button>
            <p className="ready-hint" style={{ marginTop: '12px' }}>
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
              style={{ marginTop: '16px', width: '100%' }}
            >
              📝 Open Shopping List
            </button>
            <p className="ready-hint" style={{ marginTop: '12px' }}>
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
              style={{ marginTop: '16px', width: '100%' }}
            >
              ✓ Finish Adjusting
            </button>
            <p className="ready-hint" style={{ marginTop: '12px' }}>
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
              style={{ marginTop: '16px', width: '100%' }}
            >
              📦 Open Distribution
            </button>
            <p className="ready-hint" style={{ marginTop: '12px' }}>
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
              .map((product) => {
              const needsAdjustment = run.state === 'adjusting' &&
                                       product.purchased_quantity !== null &&
                                       product.total_quantity > product.purchased_quantity
              const adjustmentOk = run.state === 'adjusting' &&
                                    product.purchased_quantity !== null &&
                                    product.total_quantity === product.purchased_quantity

              // In adjusting state, disable retract if user's bid is larger than the shortage
              const shortage = product.purchased_quantity !== null ? product.total_quantity - product.purchased_quantity : 0
              const canRetract = !adjustmentOk && !(run.state === 'adjusting' && product.current_user_bid && !product.current_user_bid.interested_only && product.current_user_bid.quantity > shortage)

              return (
              <div
                key={product.id}
                className="product-item"
                style={{
                  borderColor: needsAdjustment ? '#f59e0b' : adjustmentOk ? '#10b981' : undefined,
                  backgroundColor: needsAdjustment ? '#fffbeb' : adjustmentOk ? '#f0fdf4' : undefined
                }}
              >
                <div className="product-header">
                  <h4>{product.name}</h4>
                  <span className="product-price">${product.base_price}</span>
                </div>

                {run.state === 'adjusting' && product.purchased_quantity !== null && (
                  <div className="adjustment-info" style={{
                    padding: '8px 12px',
                    backgroundColor: needsAdjustment ? '#fef3c7' : '#d1fae5',
                    borderRadius: '6px',
                    marginBottom: '12px',
                    fontSize: '14px'
                  }}>
                    <strong>Purchased:</strong> {product.purchased_quantity} | <strong>Requested:</strong> {product.total_quantity}
                    {needsAdjustment && (
                      <span style={{ color: '#d97706', fontWeight: 'bold', marginLeft: '8px' }}>
                        ⚠ Reduce by {product.total_quantity - product.purchased_quantity}
                      </span>
                    )}
                    {adjustmentOk && (
                      <span style={{ color: '#059669', fontWeight: 'bold', marginLeft: '8px' }}>
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
                            onClick={() => handlePlaceBid(product)}
                            className="edit-bid-button"
                            title={adjustmentOk ? "No adjustment needed" : "Edit bid"}
                            disabled={adjustmentOk}
                            style={adjustmentOk ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
                          >
                            ✏️
                          </button>
                          <button
                            onClick={() => handleRetractBid(product)}
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
                        onClick={() => handlePlaceBid(product)}
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
            })}
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

      {showBidPopup && selectedProduct && (
        <BidPopup
          productName={selectedProduct.name}
          currentQuantity={selectedProduct.current_user_bid?.quantity}
          onSubmit={handleSubmitBid}
          onCancel={handleCancelBid}
          adjustingMode={run?.state === 'adjusting'}
          minAllowed={
            run?.state === 'adjusting' && selectedProduct.current_user_bid && selectedProduct.purchased_quantity !== null
              ? Math.max(0, selectedProduct.current_user_bid.quantity - (selectedProduct.total_quantity - selectedProduct.purchased_quantity))
              : undefined
          }
          maxAllowed={
            run?.state === 'adjusting' && selectedProduct.current_user_bid
              ? selectedProduct.current_user_bid.quantity
              : undefined
          }
        />
      )}

      {showAddProductPopup && (
        <AddProductPopup
          runId={runId}
          onProductSelected={handleProductSelected}
          onCancel={handleCancelAddProduct}
        />
      )}
    </div>
  )
}