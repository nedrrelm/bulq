import { useState, useEffect } from 'react'
import './ProductPage.css'

interface PriceEntry {
  price: number
  notes: string
  run_id: string
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

export default function ProductPage({ productId, onBack }: ProductPageProps) {
  const [product, setProduct] = useState<ProductDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const BACKEND_URL = 'http://localhost:8000'

  useEffect(() => {
    const fetchProduct = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${BACKEND_URL}/products/${productId}`, {
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

                    <div className="price-history">
                      <h4>Price History</h4>
                      <div className="price-entries">
                        {allPrices
                          .sort((a, b) => b.price - a.price)
                          .map((entry, index) => (
                            <div key={index} className="price-entry">
                              <span className="price-amount">${entry.price.toFixed(2)}</span>
                              {entry.notes && <span className="price-notes">{entry.notes}</span>}
                            </div>
                          ))}
                      </div>
                    </div>
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
