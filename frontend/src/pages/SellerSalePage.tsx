import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, Plus, Trash2, Play, Square, XCircle } from 'lucide-react'
import {
  useSaleDetail,
  useAddSaleProduct,
  useRemoveSaleProduct,
  useActivateSale,
  useDeactivateSale,
  useCancelSale,
} from '../hooks/queries/useSales'
import { productsApi } from '../api/products'
import { getErrorMessage } from '../utils/errorHandling'
import { logger } from '../utils/logger'
import '../styles/pages/SellerDashboardPage.css'

export default function SellerSalePage() {
  const { t } = useTranslation(['seller'])
  const { saleId } = useParams<{ saleId: string }>()
  const navigate = useNavigate()
  const { data: sale, isLoading } = useSaleDetail(saleId)

  const addProduct = useAddSaleProduct(saleId || '')
  const removeProduct = useRemoveSaleProduct(saleId || '')
  const activateSale = useActivateSale(saleId || '')
  const deactivateSale = useDeactivateSale(saleId || '')
  const cancelSale = useCancelSale(saleId || '')

  const [showAddProduct, setShowAddProduct] = useState(false)
  const [productSearch, setProductSearch] = useState('')
  const [searchResults, setSearchResults] = useState<Array<{ id: string; name: string; brand: string | null }>>([])
  const [selectedProductId, setSelectedProductId] = useState('')
  const [price, setPrice] = useState('')
  const [quantity, setQuantity] = useState('')
  const [error, setError] = useState('')

  const isPlanning = sale?.state === 'planning'
  const isActive = sale?.state === 'active'

  const handleSearchProducts = async (query: string) => {
    setProductSearch(query)
    if (query.length < 2) {
      setSearchResults([])
      return
    }
    try {
      const results = await productsApi.search(query)
      setSearchResults(results.map(p => ({ id: p.id, name: p.name, brand: p.brand })))
    } catch (err) {
      logger.error('Product search failed:', err)
    }
  }

  const handleAddProduct = () => {
    if (!selectedProductId) return
    setError('')

    addProduct.mutate(
      {
        product_id: selectedProductId,
        price: price ? parseFloat(price) : null,
        available_quantity: quantity ? parseFloat(quantity) : null,
      },
      {
        onSuccess: () => {
          setShowAddProduct(false)
          setSelectedProductId('')
          setPrice('')
          setQuantity('')
          setProductSearch('')
          setSearchResults([])
        },
        onError: (err) => {
          setError(getErrorMessage(err, t('seller:sale.errors.addProductFailed')))
        },
      }
    )
  }

  if (isLoading) return <div className="seller-page"><p>Loading...</p></div>
  if (!sale) return <div className="seller-page"><p>Sale not found</p></div>

  return (
    <div className="seller-page">
      <button className="btn btn-secondary" onClick={() => navigate('/seller')} style={{ marginBottom: '1rem' }}>
        <ArrowLeft size={16} /> Back
      </button>

      {/* Sale Header */}
      <div className="card">
        <div className="seller-profile-header">
          <div>
            <h2>{sale.title}</h2>
            {sale.description && <p className="seller-description">{sale.description}</p>}
          </div>
          <span className={`state-badge state-${sale.state}`}>{sale.state}</span>
        </div>
      </div>

      {/* State Actions */}
      <div style={{ display: 'flex', gap: '0.5rem', margin: '1rem 0' }}>
        {isPlanning && sale.products.length > 0 && (
          <button
            className="btn btn-success"
            onClick={() => activateSale.mutate()}
            disabled={activateSale.isPending}
          >
            <Play size={16} /> {t('seller:sale.actions.activate')}
          </button>
        )}
        {isActive && (
          <button
            className="btn btn-secondary"
            onClick={() => deactivateSale.mutate()}
            disabled={deactivateSale.isPending}
          >
            <Square size={16} /> {t('seller:sale.actions.deactivate')}
          </button>
        )}
        {(isPlanning || isActive) && (
          <button
            className="btn btn-secondary"
            onClick={() => {
              if (confirm(t('seller:sale.confirmCancel'))) {
                cancelSale.mutate()
              }
            }}
            disabled={cancelSale.isPending}
            style={{ marginLeft: 'auto' }}
          >
            <XCircle size={16} /> {t('seller:sale.actions.cancel')}
          </button>
        )}
      </div>

      {/* Products */}
      <div className="card">
        <div className="seller-profile-header">
          <h3>{t('seller:sale.products')} ({sale.products.length})</h3>
          {isPlanning && (
            <button className="btn btn-primary" onClick={() => setShowAddProduct(true)}>
              <Plus size={16} /> {t('seller:sale.actions.addProduct')}
            </button>
          )}
        </div>

        {sale.products.length === 0 ? (
          <div className="empty-state">
            <p>{t('seller:sale.noProducts')}</p>
          </div>
        ) : (
          <div className="sale-products-list">
            {sale.products.map((sp) => (
              <div key={sp.id} className="sale-product-item">
                <div className="sale-product-info">
                  <strong>{sp.product_name}</strong>
                  {sp.product_brand && <span className="product-brand"> ({sp.product_brand})</span>}
                  {sp.product_unit && <span className="product-unit"> [{sp.product_unit}]</span>}
                </div>
                <div className="sale-product-details">
                  {sp.price && <span className="product-price">{sp.price} RSD</span>}
                  {sp.available_quantity && <span className="product-qty">qty: {sp.available_quantity}</span>}
                </div>
                {isPlanning && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => removeProduct.mutate(sp.product_id)}
                    disabled={removeProduct.isPending}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Product Form */}
      {showAddProduct && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <h3>{t('seller:sale.actions.addProduct')}</h3>
          <div className="form-group">
            <label className="form-label">{t('seller:sale.searchProduct')}</label>
            <input
              className="form-input"
              type="text"
              value={productSearch}
              onChange={(e) => handleSearchProducts(e.target.value)}
              placeholder={t('seller:sale.searchProductPlaceholder')}
            />
            {searchResults.length > 0 && !selectedProductId && (
              <div className="product-search-results">
                {searchResults.map(p => (
                  <div
                    key={p.id}
                    className="product-search-item"
                    onClick={() => {
                      setSelectedProductId(p.id)
                      setProductSearch(p.name + (p.brand ? ` (${p.brand})` : ''))
                      setSearchResults([])
                    }}
                  >
                    {p.name}{p.brand ? ` (${p.brand})` : ''}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">{t('seller:sale.price')}</label>
              <input
                className="form-input"
                type="number"
                step="0.01"
                min="0"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder={t('seller:sale.pricePlaceholder')}
              />
            </div>
            <div className="form-group" style={{ flex: 1 }}>
              <label className="form-label">{t('seller:sale.quantity')}</label>
              <input
                className="form-input"
                type="number"
                step="0.01"
                min="0"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder={t('seller:sale.quantityPlaceholder')}
              />
            </div>
          </div>
          {error && <div className="alert alert-error">{error}</div>}
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
            <button
              className="btn btn-primary"
              onClick={handleAddProduct}
              disabled={!selectedProductId || addProduct.isPending}
            >
              {addProduct.isPending ? 'Adding...' : t('seller:sale.actions.addProduct')}
            </button>
            <button className="btn btn-secondary" onClick={() => { setShowAddProduct(false); setError('') }}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
