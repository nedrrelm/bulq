import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import '../styles/components/AddProductPopup.css'
import { runsApi } from '../api'
import type { AvailableProduct } from '../types/product'
import NewProductPopup from './NewProductPopup'
import { getErrorMessage } from '../utils/errorHandling'
import BaseModal from '../common/BaseModal'

interface AddProductPopupProps {
  runId: string
  onProductSelected: (product: AvailableProduct) => void
  onCancel: () => void
}

export default function AddProductPopup({ runId, onProductSelected, onCancel }: AddProductPopupProps) {
  const { t } = useTranslation(['common', 'product'])
  const [products, setProducts] = useState<AvailableProduct[]>([])
  const [filteredProducts, setFilteredProducts] = useState<AvailableProduct[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [showNewProductPopup, setShowNewProductPopup] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const fetchAvailableProducts = async () => {
      try {
        setLoading(true)
        setError('')

        const productsData = await runsApi.getAvailableProducts(runId)
        setProducts(productsData)
        setFilteredProducts(productsData)
      } catch (err) {
        setError(getErrorMessage(err, t('product:errors.loadFailed')))
      } finally {
        setLoading(false)
      }
    }

    fetchAvailableProducts()
  }, [runId, t])

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

  const handleNewProductSuccess = async () => {
    setShowNewProductPopup(false)
    // Refresh the available products list
    try {
      setLoading(true)
      const productsData = await runsApi.getAvailableProducts(runId)
      setProducts(productsData)
      setFilteredProducts(productsData)
    } catch (err) {
      setError(getErrorMessage(err, t('product:errors.reloadFailed')))
    } finally {
      setLoading(false)
    }
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
      const selectedProduct = filteredProducts[selectedIndex]
      if (selectedIndex >= 0 && selectedIndex < filteredProducts.length && selectedProduct) {
        handleProductSelect(selectedProduct)
      }
    }
  }

  return (
    <>
      <BaseModal
        isOpen={true}
        onClose={onCancel}
        size="md"
        className="add-product-popup"
        showHeader={false}
        asForm={false}
        error={error}
        cancelButton={{
          text: t('common:buttons.cancel'),
          onClick: onCancel,
          variant: 'secondary'
        }}
        customActions={
          <>
            {!loading && !error && filteredProducts.length > 0 && (
              <>
                <button
                  onClick={() => setShowNewProductPopup(true)}
                  className="btn btn-secondary"
                >
                  {t('product:actions.createNew')}
                </button>
                <p className="keyboard-hint">
                  {t('product:addToRun.keyboardHint')}
                </p>
              </>
            )}
          </>
        }
      >
        <h3>{t('product:addToRun.title')}</h3>
        <p className="popup-description">{t('product:addToRun.description')}</p>

        <div className="search-container">
          <input
            ref={inputRef}
            type="text"
            placeholder={t('product:addToRun.searchPlaceholder')}
            value={searchTerm}
            onChange={handleSearchChange}
            onKeyDown={handleKeyDown}
            className="search-input"
          />
        </div>

        {loading && (
          <div className="loading-state">
            <p>{t('product:states.loading')}</p>
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
                  <>
                    <p>{t('product:addToRun.noMatch', { term: searchTerm })}</p>
                    <button
                      onClick={() => setShowNewProductPopup(true)}
                      className="btn btn-primary create-product-button"
                    >
                      {t('product:actions.createNew')}
                    </button>
                  </>
                ) : (
                  <>
                    <p>{t('product:addToRun.allProductsHaveBids')}</p>
                    <button
                      onClick={() => setShowNewProductPopup(true)}
                      className="btn btn-primary create-product-button"
                    >
                      {t('product:actions.createNew')}
                    </button>
                  </>
                )}
              </div>
            ) : (
              <div className="products-list">
                {filteredProducts.map((product, index) => (
                  <div
                    key={product.id}
                    className={`product-option ${index === selectedIndex ? 'selected' : ''} ${product.has_store_availability ? 'at-store' : 'other-store'}`}
                    onClick={() => handleProductSelect(product)}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    <div className="product-info">
                      <span className="product-name">
                        {product.has_store_availability && <span className="store-badge">✓</span>}
                        {product.name}
                      </span>
                      {product.current_price && <span className="product-price">${product.current_price}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </BaseModal>

      {showNewProductPopup && (
        <NewProductPopup
          onClose={() => setShowNewProductPopup(false)}
          onSuccess={handleNewProductSuccess}
        />
      )}
    </>
  )
}
