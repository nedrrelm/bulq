import { useState, useEffect, useMemo } from 'react'
import '../styles/components/ProductPage.css'
import { productsApi } from '../api'
import LoadingSpinner from './LoadingSpinner'
import '../styles/components/LoadingSpinner.css'
import ErrorAlert from './ErrorAlert'
import { getErrorMessage } from '../utils/errorHandling'
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

interface PriceEntry {
  price: number
  notes: string
  run_id?: string
  timestamp: string | null
}

interface StoreData {
  store_id: string
  store_name: string
  current_price: number | null
  price_history: PriceEntry[]
  notes: string
}

interface ProductDetails {
  id: string
  name: string
  brand: string | null
  unit: string | null
  stores: StoreData[]
}

interface ProductPageProps {
  productId: string
  onBack: () => void
}

// Color palette for stores
const STORE_COLORS = ['#667eea', '#f56565', '#48bb78', '#ed8936', '#9f7aea', '#38b2ac', '#ed64a6']

// Custom tooltip component
function CustomTooltip(props: any) {
  const { active, payload } = props
  if (!active || !payload || !payload.length || !payload[0]) {
    return null
  }

  const data = payload[0].payload as { store_name: string; price: number; timestamp: string; notes?: string }
  return (
    <div className="custom-tooltip">
      <p className="tooltip-store">{data.store_name}</p>
      <p className="tooltip-price">${data.price.toFixed(2)}</p>
      <p className="tooltip-date">{new Date(data.timestamp).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      })}</p>
      {data.notes && <p className="tooltip-notes">{data.notes}</p>}
    </div>
  )
}

function PriceGraph({ storesData }: { storesData: StoreData[] }) {
  // Transform data for Recharts - memoized to prevent recalculation
  const chartData = useMemo(() => {
    const storeDataArray = storesData.map((store, idx) => ({
      store_id: store.store_id,
      store_name: store.store_name,
      color: STORE_COLORS[idx % STORE_COLORS.length],
      data: store.price_history
        .filter(p => p.timestamp)
        .map(p => ({
          timestamp: new Date(p.timestamp!).getTime(),
          price: p.price,
          notes: p.notes,
          store_name: store.store_name
        }))
    }))

    // Check if we have any data
    const hasData = storeDataArray.some(s => s.data.length > 0)

    return { storeDataArray, hasData }
  }, [storesData])

  if (!chartData.hasData) {
    return <p className="no-graph-data">No historical price data available</p>
  }

  // Format timestamp for X-axis
  const formatXAxis = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <div className="price-graph">
      <h4>Price History Across All Stores</h4>

      <ResponsiveContainer width="100%" height={350}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis
            type="number"
            dataKey="timestamp"
            name="Date"
            tickFormatter={formatXAxis}
            domain={['auto', 'auto']}
            stroke="#666"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            type="number"
            dataKey="price"
            name="Price"
            tickFormatter={(value) => `$${value.toFixed(2)}`}
            domain={['auto', 'auto']}
            stroke="#666"
            style={{ fontSize: '12px' }}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
          <Legend
            wrapperStyle={{ paddingTop: '10px' }}
            iconType="circle"
          />
          {chartData.storeDataArray.map((store) => (
            <Scatter
              key={store.store_id}
              name={store.store_name}
              data={store.data}
              fill={store.color}
              shape="circle"
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function ProductPage({ productId, onBack }: ProductPageProps) {
  const [product, setProduct] = useState<ProductDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchProduct = async () => {
    try {
      setLoading(true)
      setError('')

      const data = await productsApi.getProduct(productId)
      setProduct(data as any)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load product'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProduct()
  }, [productId])

  if (loading) {
    return <LoadingSpinner />
  }

  if (error || !product) {
    return <ErrorAlert message={error || 'Product not found'} onRetry={fetchProduct} />
  }

  return (
    <div className="product-page">
      <div className="breadcrumb">
        <span onClick={onBack} className="breadcrumb-link">Dashboard</span>
        <span className="breadcrumb-separator">›</span>
        <span>{product.name}</span>
      </div>

      <div className="product-header">
        <h2>{product.name}</h2>
        {(product.brand || product.unit) && (
          <div className="product-meta">
            {product.brand && <span className="meta-item">Brand: {product.brand}</span>}
            {product.unit && <span className="meta-item">Unit: {product.unit}</span>}
          </div>
        )}
      </div>

      {product.stores.length === 0 && (
        <div className="empty-state">
          <p>No store information available for this product.</p>
        </div>
      )}

      {product.stores.length > 0 && (
        <>
          {/* Single combined price graph */}
          <PriceGraph storesData={product.stores} />

          {/* Store cards with current prices and stats */}
          <div className="stores-comparison">
            {product.stores.map((store) => {
              const allPrices = store.price_history || []

              // Calculate min/max/avg prices for this store
              const prices = allPrices.map(p => p.price)
              const minPrice = prices.length > 0 ? Math.min(...prices) : null
              const maxPrice = prices.length > 0 ? Math.max(...prices) : null
              const avgPrice = prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : null

              return (
                <div key={store.store_id} className="store-card card">
                  <div className="store-header">
                    <h3>{store.store_name}</h3>
                    {store.current_price && (
                      <div className="current-price">
                        <span className="price-label">Current Price:</span>
                        <span className="price-value">${store.current_price.toFixed(2)}</span>
                      </div>
                    )}
                  </div>

                  {allPrices.length === 0 ? (
                    <p className="no-price-data">No price history available</p>
                  ) : (
                    <div className="price-summary">
                      {minPrice !== null && (
                        <div className="price-stat">
                          <span className="price-label">Lowest</span>
                          <span className="price-value price-min">${minPrice.toFixed(2)}</span>
                        </div>
                      )}
                      {avgPrice !== null && (
                        <div className="price-stat">
                          <span className="price-label">Average</span>
                          <span className="price-value">${avgPrice.toFixed(2)}</span>
                        </div>
                      )}
                      {maxPrice !== null && maxPrice !== minPrice && (
                        <div className="price-stat">
                          <span className="price-label">Highest</span>
                          <span className="price-value price-max">${maxPrice.toFixed(2)}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
