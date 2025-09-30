import { useState, useRef, useEffect } from 'react'
import './AddProductPopup.css'

interface AvailableProduct {
  id: string
  name: string
  base_price: string
}

interface AddProductPopupProps {
  runId: string
  onProductSelected: (product: AvailableProduct) => void
  onCancel: () => void
}

export default function AddProductPopup({ runId, onProductSelected, onCancel }: AddProductPopupProps) {
  const [products, setProducts] = useState<AvailableProduct[]>([])
  const [filteredProducts, setFilteredProducts] = useState<AvailableProduct[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)

  const BACKEND_URL = 'http://localhost:8000'

  useEffect(() => {
    const fetchAvailableProducts = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${BACKEND_URL}/runs/${runId}/available-products`, {
          credentials: 'include'
        })

        if (!response.ok) {
          throw new Error('Failed to fetch available products')
        }

        const productsData: AvailableProduct[] = await response.json()
        setProducts(productsData)
        setFilteredProducts(productsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load products')
      } finally {
        setLoading(false)
      }
    }

    fetchAvailableProducts()
  }, [runId])

  useEffect(() => {
    // Autofocus the input when component mounts
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])

  useEffect(() => {
    // Filter products based on search term
    const filtered = products.filter(product =>
      product.name.toLowerCase().includes(searchTerm.toLowerCase())
    )
    setFilteredProducts(filtered)
    setSelectedIndex(-1)
  }, [searchTerm, products])

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value)
  }

  const handleProductSelect = (product: AvailableProduct) => {
    onProductSelected(product)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(prev =>
        prev < filteredProducts.length - 1 ? prev + 1 : prev
      )
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(prev => prev > 0 ? prev - 1 : -1)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (selectedIndex >= 0 && selectedIndex < filteredProducts.length) {
        handleProductSelect(filteredProducts[selectedIndex])
      }
    }
  }

  return (
    <div className="add-product-popup-overlay" onClick={onCancel}>
      <div className="add-product-popup" onClick={(e) => e.stopPropagation()}>
        <h3>Add Product to Run</h3>
        <p className="popup-description">Select a product to start bidding on</p>

        <div className="search-container">
          <input
            ref={inputRef}
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={handleSearchChange}
            onKeyDown={handleKeyDown}
            className="search-input"
          />
        </div>

        {loading && (
          <div className="loading-state">
            <p>Loading products...</p>
          </div>
        )}

        {error && (
          <div className="error-state">
            <p>❌ {error}</p>
          </div>
        )}

        {!loading && !error && (
          <div className="products-dropdown">
            {filteredProducts.length === 0 ? (
              <div className="no-products-state">
                {searchTerm ? (
                  <p>No products found matching "{searchTerm}"</p>
                ) : (
                  <p>All products from this store already have bids!</p>
                )}
              </div>
            ) : (
              <div className="products-list">
                {filteredProducts.map((product, index) => (
                  <div
                    key={product.id}
                    className={`product-option ${index === selectedIndex ? 'selected' : ''}`}
                    onClick={() => handleProductSelect(product)}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    <div className="product-info">
                      <span className="product-name">{product.name}</span>
                      <span className="product-price">${product.base_price}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="popup-footer">
          <button onClick={onCancel} className="cancel-button">
            Cancel
          </button>
          {filteredProducts.length > 0 && (
            <p className="keyboard-hint">
              Use ↑↓ arrow keys and Enter to select
            </p>
          )}
        </div>
      </div>
    </div>
  )
}