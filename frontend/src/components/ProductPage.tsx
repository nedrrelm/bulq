import { useState, useEffect } from 'react'
import './ProductPage.css'
import { API_BASE_URL } from '../config'

interface PriceEntry {
  price: number
  notes: string
  run_id: string
  timestamp?: string
}

interface StoreData {
  store_id: string
  store_name: string
  base_price: number | null
  encountered_prices: PriceEntry[]
  product_id: string
}

interface ProductDetails {
  id: string
  name: string
  stores: StoreData[]
}

interface ProductPageProps {
  productId: string
  onBack: () => void
}

function PriceGraph({ prices }: { prices: PriceEntry[] }) {
  // Filter prices with timestamps and sort by date
  const pricesWithTime = prices
    .filter(p => p.timestamp)
    .map(p => ({
      ...p,
      date: new Date(p.timestamp!)
    }))
    .sort((a, b) => a.date.getTime() - b.date.getTime())

  if (pricesWithTime.length === 0) {
    return <p className="no-graph-data">No historical price data available</p>
  }

  // Calculate graph dimensions and scales
  const allPrices = pricesWithTime.map(p => p.price)
  const minPrice = Math.min(...allPrices)
  const maxPrice = Math.max(...allPrices)
  const priceRange = maxPrice - minPrice || 1
  const padding = priceRange * 0.1

  const graphHeight = 200
  const graphWidth = 600
  const marginLeft = 60
  const marginRight = 30
  const marginTop = 10
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
  const minTime = pricesWithTime[0].date.getTime()
  const maxTime = pricesWithTime[pricesWithTime.length - 1].date.getTime()
  const timeRange = maxTime - minTime || 1

  const dateToX = (date: Date) => {
    return marginLeft + ((date.getTime() - minTime) / timeRange) * plotWidth
  }

  return (
    <div className="price-graph">
      <h4>Price Over Time</h4>
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

        {/* Data points with horizontal lines */}
        {pricesWithTime.map((p, i) => (
          <line
            key={`hline-${i}`}
            x1={marginLeft}
            y1={priceToY(p.price)}
            x2={dateToX(p.date)}
            y2={priceToY(p.price)}
            stroke="#e0e0e0"
            strokeWidth="1"
            strokeDasharray="2,2"
            opacity="0.5"
          />
        ))}

        {/* Data points */}
        {pricesWithTime.map((p, i) => (
          <g key={i}>
            <circle
              cx={dateToX(p.date)}
              cy={priceToY(p.price)}
              r={6}
              className="price-point"
            />
            <title>{`$${p.price.toFixed(2)} - ${p.date.toLocaleDateString()} ${p.notes ? `(${p.notes})` : ''}`}</title>
          </g>
        ))}

        {/* X-axis labels */}
        {pricesWithTime.map((p, i) => {
          if (i % Math.ceil(pricesWithTime.length / 4) === 0 || i === pricesWithTime.length - 1) {
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

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
          credentials: 'include'
        })

        if (!response.ok) {
          throw new Error(`Failed to load product: ${response.status}`)
        }

        const data: ProductDetails = await response.json()
        setProduct(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load product')
      } finally {
        setLoading(false)
      }
    }

    fetchProduct()
  }, [productId])

  if (loading) {
    return (
      <div className="product-page">
        <button onClick={onBack} className="btn btn-secondary">← Back</button>
        <p>Loading product...</p>
      </div>
    )
  }

  if (error || !product) {
    return (
      <div className="product-page">
        <button onClick={onBack} className="btn btn-secondary">← Back</button>
        <div className="alert alert-error">
          {error || 'Product not found'}
        </div>
      </div>
    )
  }

  return (
    <div className="product-page">
      <div className="breadcrumb">
        <span onClick={onBack} className="breadcrumb-link">Dashboard</span>
        <span className="breadcrumb-separator">›</span>
        <span>{product.name}</span>
      </div>

      <h2>{product.name}</h2>

      {product.stores.length === 0 && (
        <div className="empty-state">
          <p>No store information available for this product.</p>
        </div>
      )}

      {product.stores.length > 0 && (
        <div className="stores-comparison">
          {product.stores.map((store) => {
            const allPrices = [...store.encountered_prices]
            if (store.base_price) {
              allPrices.push({ price: store.base_price, notes: 'Base price', run_id: '' })
            }

            // Calculate min/max/avg prices
            const prices = allPrices.map(p => p.price)
            const minPrice = prices.length > 0 ? Math.min(...prices) : null
            const maxPrice = prices.length > 0 ? Math.max(...prices) : null
            const avgPrice = prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : null

            return (
              <div key={store.store_id} className="store-card card">
                <h3>{store.store_name}</h3>

                {allPrices.length === 0 ? (
                  <p className="no-price-data">No price data available</p>
                ) : (
                  <>
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

                    <PriceGraph prices={allPrices} />
                  </>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
