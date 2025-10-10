import { useState, useEffect } from 'react'
import '../styles/components/ProductPage.css'
import { productsApi, ApiError } from '../api'
import LoadingSpinner from './LoadingSpinner'
import '../styles/components/LoadingSpinner.css'
import ErrorAlert from './ErrorAlert'

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

interface PriceWithStore extends PriceEntry {
  store_id: string
  store_name: string
  date: Date
}

function PriceGraph({ storesData }: { storesData: StoreData[] }) {
  // Combine all prices from all stores
  const allPricesWithStore: PriceWithStore[] = []
  storesData.forEach(store => {
    store.price_history
      .filter(p => p.timestamp)
      .forEach(p => {
        allPricesWithStore.push({
          ...p,
          store_id: store.store_id,
          store_name: store.store_name,
          date: new Date(p.timestamp!)
        })
      })
  })

  // Sort by date
  allPricesWithStore.sort((a, b) => a.date.getTime() - b.date.getTime())

  if (allPricesWithStore.length === 0) {
    return <p className="no-graph-data">No historical price data available</p>
  }

  // Generate colors for stores
  const storeColors = new Map<string, string>()
  const colors = ['#667eea', '#f56565', '#48bb78', '#ed8936', '#9f7aea', '#38b2ac', '#ed64a6']
  storesData.forEach((store, idx) => {
    storeColors.set(store.store_id, colors[idx % colors.length])
  })

  // Calculate graph dimensions and scales
  const allPrices = allPricesWithStore.map(p => p.price)
  const minPrice = Math.min(...allPrices)
  const maxPrice = Math.max(...allPrices)
  const priceRange = maxPrice - minPrice || 1
  const padding = priceRange * 0.1

  const graphHeight = 300
  const graphWidth = 700
  const marginLeft = 60
  const marginRight = 30
  const marginTop = 40
  const marginBottom = 30
  const plotWidth = graphWidth - marginLeft - marginRight
  const plotHeight = graphHeight - marginTop - marginBottom

  const yMin = minPrice - padding
  const yMax = maxPrice + padding
  const yRange = yMax - yMin

  // Convert price to y-coordinate
  const priceToY = (price: number) => {
    return marginTop + plotHeight - ((price - yMin) / yRange) * plotHeight
  }

  // Convert date to x-coordinate
  const minTime = allPricesWithStore[0].date.getTime()
  const maxTime = allPricesWithStore[allPricesWithStore.length - 1].date.getTime()
  const timeRange = maxTime - minTime || 1

  const dateToX = (date: Date) => {
    return marginLeft + ((date.getTime() - minTime) / timeRange) * plotWidth
  }

  return (
    <div className="price-graph">
      <h4>Price History Across All Stores</h4>

      {/* Legend */}
      <div className="graph-legend">
        {storesData.map(store => (
          <div key={store.store_id} className="legend-item">
            <span
              className="legend-dot"
              style={{ backgroundColor: storeColors.get(store.store_id) }}
            />
            <span>{store.store_name}</span>
          </div>
        ))}
      </div>

      <svg width={graphWidth} height={graphHeight} className="price-chart">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map(ratio => {
          const y = marginTop + plotHeight * (1 - ratio)
          const price = yMin + yRange * ratio
          return (
            <g key={ratio}>
              <line
                x1={marginLeft}
                y1={y}
                x2={graphWidth - marginRight}
                y2={y}
                className="grid-line"
              />
              <text x={5} y={y + 4} className="y-axis-label">
                ${price.toFixed(2)}
              </text>
            </g>
          )
        })}

        {/* Data points */}
        {allPricesWithStore.map((p, i) => (
          <g key={i}>
            <circle
              cx={dateToX(p.date)}
              cy={priceToY(p.price)}
              r={6}
              fill={storeColors.get(p.store_id)}
              className="price-point"
              stroke="white"
              strokeWidth="2"
            />
            <title>{`${p.store_name}: $${p.price.toFixed(2)} - ${p.date.toLocaleDateString()} ${p.notes ? `(${p.notes})` : ''}`}</title>
          </g>
        ))}

        {/* X-axis labels */}
        {allPricesWithStore.map((p, i) => {
          if (i % Math.ceil(allPricesWithStore.length / 5) === 0 || i === allPricesWithStore.length - 1) {
            return (
              <text
                key={i}
                x={dateToX(p.date)}
                y={graphHeight - 10}
                className="x-axis-label"
                textAnchor="middle"
              >
                {p.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </text>
            )
          }
          return null
        })}
      </svg>
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
      setError(err instanceof Error ? err.message : 'Failed to load product')
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
