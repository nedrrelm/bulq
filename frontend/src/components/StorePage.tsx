import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import '../styles/components/StorePage.css'
import LoadingSpinner from './LoadingSpinner'
import '../styles/components/LoadingSpinner.css'
import ErrorAlert from './ErrorAlert'
import RunCard from './RunCard'

interface Product {
  id: string
  name: string
  brand: string | null
  unit: string | null
  current_price: string | null
}

interface ActiveRun {
  id: string
  state: string
  group_id: string
  group_name: string
  store_name: string
  leader_name: string
  planned_on: string | null
}

interface StorePageData {
  store: {
    id: string
    name: string
  }
  products: Product[]
  active_runs: ActiveRun[]
}

interface StorePageProps {
  storeId: string
  onBack: () => void
}

function StorePage({ storeId, onBack }: StorePageProps) {
  const [data, setData] = useState<StorePageData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStoreData()
  }, [storeId])

  const fetchStoreData = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`http://localhost:8000/stores/${storeId}`, {
        credentials: 'include'
      })

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Store not found')
        }
        throw new Error('Failed to load store data')
      }

      const storeData = await response.json()
      setData(storeData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  if (error) {
    return (
      <div className="store-page">
        <button className="btn btn-secondary back-btn" onClick={onBack}>
          ← Back
        </button>
        <ErrorAlert message={error} />
      </div>
    )
  }

  if (!data) {
    return null
  }

  return (
    <div className="store-page">
      <button className="btn btn-secondary back-btn" onClick={onBack}>
        ← Back
      </button>

      <div className="store-header">
        <h1>{data.store.name}</h1>
      </div>

      {data.active_runs.length > 0 && (
        <section className="active-runs-section">
          <h2>Active Runs ({data.active_runs.length})</h2>
          <div className="active-runs-list">
            {data.active_runs.map(run => (
              <RunCard key={run.id} run={run} showGroupName={true} />
            ))}
          </div>
        </section>
      )}

      <section className="products-section">
        <h2>Products</h2>
        {data.products.length === 0 ? (
          <div className="empty-state">
            <p>No products with recorded prices yet</p>
            <p className="empty-state-hint">
              Products will appear here once availability is added during shopping runs
            </p>
          </div>
        ) : (
          <div className="products-list">
            {data.products.map(product => (
              <Link
                key={product.id}
                to={`/products/${product.id}`}
                className="product-card card"
              >
                <div className="product-info">
                  <div className="product-name">{product.name}</div>
                  {product.brand && (
                    <div className="product-brand">{product.brand}</div>
                  )}
                  <div className="product-details">
                    {product.unit && <span className="product-unit">{product.unit}</span>}
                    {product.current_price && (
                      <span className="product-price">≈ ${product.current_price}</span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default StorePage
