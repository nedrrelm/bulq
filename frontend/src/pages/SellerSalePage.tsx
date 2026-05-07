import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, Plus, Trash2, Play, Square, XCircle, CheckCircle, Package } from 'lucide-react'
import {
  useSaleDetail,
  useAddSaleProduct,
  useRemoveSaleProduct,
  useActivateSale,
  useDeactivateSale,
  useCancelSale,
  useConfirmSale,
  useStartDistributing,
} from '../hooks/queries/useSales'
import { productsApi } from '../api/products'
import { salesApi } from '../api/sales'
import { getErrorMessage } from '../utils/errorHandling'
import { logger } from '../utils/logger'
import '../styles/run-states.css'
import '../styles/pages/SellerDashboardPage.css'
import '../styles/pages/RunPage.css'

interface DistGroupEntry {
  item_id: string
  run_id: string
  group_id: string
  group_name: string
  leader_name: string
  quantity: number
  is_handed_over: boolean
  handed_over_at: string | null
}

interface DistProduct {
  product_id: string
  product_name: string
  product_unit: string | null
  total_quantity: number
  groups: DistGroupEntry[]
}

interface DistData {
  sale_id: string
  state: string
  products: DistProduct[]
  total_items: number
  handed_over_count: number
}

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
  const confirmSale = useConfirmSale(saleId || '')
  const startDistributing = useStartDistributing(saleId || '')

  const [showAddProduct, setShowAddProduct] = useState(false)
  const [productSearch, setProductSearch] = useState('')
  const [searchResults, setSearchResults] = useState<Array<{ id: string; name: string; brand: string | null }>>([])
  const [selectedProductId, setSelectedProductId] = useState('')
  const [price, setPrice] = useState('')
  const [quantity, setQuantity] = useState('')
  const [error, setError] = useState('')

  const [distData, setDistData] = useState<DistData | null>(null)
  const [distLoading, setDistLoading] = useState(false)
  const [toggling, setToggling] = useState<string | null>(null)
  const [expandedGroupId, setExpandedGroupId] = useState<string | null>(null)

  const isPlanning = sale?.state === 'planning'
  const isActive = sale?.state === 'active'
  const isConfirmed = sale?.state === 'confirmed'
  const isDistributing = sale?.state === 'distributing'
  const isCompleted = sale?.state === 'completed'
  const showDistribution = isDistributing || isCompleted

  const fetchDistribution = useCallback(async () => {
    if (!saleId || !showDistribution) return
    setDistLoading(true)
    try {
      const result = await salesApi.getDistribution(saleId) as DistData
      setDistData(result)
    } catch (err) {
      logger.error('Failed to load distribution:', err)
    } finally {
      setDistLoading(false)
    }
  }, [saleId, showDistribution])

  useEffect(() => {
    fetchDistribution()
  }, [fetchDistribution])

  const handleToggleHandover = async (itemId: string) => {
    if (!saleId) return
    setToggling(itemId)
    try {
      const result = await salesApi.toggleHandover(saleId, itemId) as DistData
      setDistData(result)
    } catch (err) {
      logger.error('Failed to toggle handover:', err)
    } finally {
      setToggling(null)
    }
  }

  const handleCompleteSale = async () => {
    if (!saleId) return
    try {
      await salesApi.completeSale(saleId)
      // Refetch sale detail
      window.location.reload()
    } catch (err) {
      logger.error('Failed to complete sale:', err)
    }
  }

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
          <span className={`run-state state-${sale.state}`}>{sale.state}</span>
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
          <>
            <button
              className="btn btn-primary"
              onClick={() => confirmSale.mutate()}
              disabled={confirmSale.isPending}
            >
              <CheckCircle size={16} /> {t('seller:sale.actions.confirm')}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => deactivateSale.mutate()}
              disabled={deactivateSale.isPending}
            >
              <Square size={16} /> {t('seller:sale.actions.deactivate')}
            </button>
          </>
        )}
        {isConfirmed && (
          <button
            className="btn btn-primary"
            onClick={() => startDistributing.mutate()}
            disabled={startDistributing.isPending}
          >
            <Package size={16} /> {t('seller:sale.actions.startDistributing')}
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

      {/* Distribution Section — same UI as RunDistributionSection */}
      {showDistribution && (
        <div className="distribution-section" style={{ marginTop: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3>{t('seller:distribution.title')}</h3>
            {distData && distData.total_items > 0 && distData.handed_over_count === distData.total_items && isDistributing && (
              <button className="btn btn-success" onClick={handleCompleteSale}>
                <CheckCircle size={16} /> {t('seller:distribution.completeSale')}
              </button>
            )}
          </div>

          {distLoading && <p>Loading...</p>}

          {distData && (() => {
            // Build per-group structure: each group = collapsible card with products inside
            const groupsMap = new Map<string, {
              run_id: string
              group_id: string
              group_name: string
              leader_name: string
              items: Array<DistGroupEntry & { product_name: string; product_unit: string | null }>
              all_handed: boolean
            }>()

            for (const product of distData.products) {
              for (const group of product.groups) {
                if (!groupsMap.has(group.run_id)) {
                  groupsMap.set(group.run_id, {
                    run_id: group.run_id,
                    group_id: group.group_id,
                    group_name: group.group_name,
                    leader_name: group.leader_name,
                    items: [],
                    all_handed: true,
                  })
                }
                const g = groupsMap.get(group.run_id)!
                g.items.push({ ...group, product_name: product.product_name, product_unit: product.product_unit })
                if (!group.is_handed_over) g.all_handed = false
              }
            }

            const groups = [...groupsMap.values()]

            return (
              <div className="distribution-list">
                {groups.length === 0 ? (
                  <div className="empty-state">
                    <p>{t('seller:distribution.noItems')}</p>
                  </div>
                ) : groups.map((group) => {
                  const isGroupExpanded = expandedGroupId === group.run_id

                  return (
                    <div key={group.run_id} className={`user-card ${group.all_handed ? 'completed' : ''}`}>
                      <div
                        className="user-header"
                        onClick={() => setExpandedGroupId(isGroupExpanded ? null : group.run_id)}
                      >
                        <div className="user-info">
                          <span className="user-name">{group.group_name}</span>
                          <span className="user-total">{group.leader_name}</span>
                        </div>
                        <div className="user-actions">
                          {group.all_handed && <span className="pickup-badge">{t('run:labels.pickedUp')}</span>}
                          <span className="expand-icon">{isGroupExpanded ? '▼' : '▶'}</span>
                        </div>
                      </div>

                      {isGroupExpanded && (
                        <div className="user-products">
                          <div className="user-products-header">
                            {!group.all_handed && isDistributing && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  group.items.filter(i => !i.is_handed_over).forEach(i => handleToggleHandover(i.item_id))
                                }}
                                className="mark-all-button"
                                disabled={toggling !== null}
                              >
                                {t('run:actions.markAllPickedUp')}
                              </button>
                            )}
                          </div>
                          {group.items
                            .sort((a, b) => a.product_name.localeCompare(b.product_name))
                            .map((item) => (
                              <div key={item.item_id} className={`product-item ${item.is_handed_over ? 'picked-up' : ''}`}>
                                <div className="product-info">
                                  <div className="product-name">{item.product_name}</div>
                                  <div className="product-details">
                                    <span>{item.quantity}{item.product_unit ? ` ${item.product_unit}` : ''}</span>
                                  </div>
                                </div>
                                {isDistributing && (
                                  <button
                                    onClick={() => handleToggleHandover(item.item_id)}
                                    disabled={toggling === item.item_id}
                                    className={`pickup-button ${item.is_handed_over ? 'picked-up' : ''}`}
                                  >
                                    {toggling === item.item_id
                                      ? t('run:labels.updating')
                                      : item.is_handed_over
                                        ? t('run:labels.pickedUp')
                                        : t('run:actions.markPickedUp')}
                                  </button>
                                )}
                              </div>
                            ))}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )
          })()}
        </div>
      )}
    </div>
  )
}
