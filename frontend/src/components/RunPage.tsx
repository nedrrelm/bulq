import { useState, useEffect } from 'react'
import './RunPage.css'

interface Product {
  id: string
  name: string
  base_price: string
  total_quantity: number
  interested_count: number
}

interface RunDetail {
  id: string
  group_id: string
  group_name: string
  store_id: string
  store_name: string
  state: string
  products: Product[]
}

interface RunPageProps {
  runId: string
  onBack: () => void
}

export default function RunPage({ runId, onBack }: RunPageProps) {
  const [run, setRun] = useState<RunDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const BACKEND_URL = 'http://localhost:8000'

  useEffect(() => {
    const fetchRunDetails = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${BACKEND_URL}/runs/${runId}`, {
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
          <button onClick={onBack} className="back-button">
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
          <button onClick={onBack} className="back-button">
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
          <button onClick={onBack} className="back-button">
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
      <div className="run-header">
        <button onClick={onBack} className="back-button">
          ← Back to Group
        </button>
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
      </div>

      <div className="products-section">
        <h3>Products ({run.products.length})</h3>

        {run.products.length === 0 ? (
          <div className="no-products">
            <p>No products have been added to this run yet.</p>
            {run.state === 'planning' && (
              <p>Users can start expressing interest in products to get this run started!</p>
            )}
          </div>
        ) : (
          <div className="products-list">
            {run.products.map((product) => (
              <div key={product.id} className="product-item">
                <div className="product-header">
                  <h4>{product.name}</h4>
                  <span className="product-price">${product.base_price}</span>
                </div>
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
              </div>
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

      {run.state === 'completed' && (
        <div className="actions-section">
          <div className="info-banner">
            <p>🎉 This run has been completed! Costs have been calculated and the run is finished.</p>
          </div>
        </div>
      )}
    </div>
  )
}