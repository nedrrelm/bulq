import { useState, useEffect, useMemo, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import '../styles/pages/ProductPage.css'
import { productsApi } from '../api'
import { tagsApi } from '../api'
import type { TagBrief, TagSearchResult } from '../api/tags'
import LoadingSpinner from '../components/common/LoadingSpinner'
import '../styles/components/LoadingSpinner.css'
import ErrorAlert from '../components/common/ErrorAlert'
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
  tags: TagBrief[]
}

interface ProductPageProps {
  productId: string
  onBack: () => void
}

// Color palette for stores
const STORE_COLORS = ['#667eea', '#f56565', '#48bb78', '#ed8936', '#9f7aea', '#38b2ac', '#ed64a6']

// Custom tooltip component
interface CustomTooltipProps {
  active?: boolean
  payload?: Array<{
    payload: {
      store_name: string
      price: number
      timestamp: string
      notes?: string
    }
  }>
}

function CustomTooltip(props: CustomTooltipProps) {
  const { active, payload } = props
  if (!active || !payload || !payload.length || !payload[0]) {
    return null
  }

  const data = payload[0].payload as { store_name: string; price: number; timestamp: string; notes?: string }
  return (
    <div className="custom-tooltip">
      <p className="tooltip-store">{data.store_name}</p>
      <p className="tooltip-price">{data.price.toFixed(2)} RSD</p>
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
  const { t } = useTranslation(['product'])
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
    return <p className="no-graph-data">{t('product:priceHistory.noData')}</p>
  }

  // Format timestamp for X-axis
  const formatXAxis = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <div className="price-graph">
      <h4>{t('product:priceHistory.title')}</h4>

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
            tickFormatter={(value) => `${value.toFixed(2)} RSD`}
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
  const { t } = useTranslation(['common', 'product', 'admin'])
  const navigate = useNavigate()
  const [product, setProduct] = useState<ProductDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showTagSelector, setShowTagSelector] = useState(false)
  const [tagSearch, setTagSearch] = useState('')
  const [tagResults, setTagResults] = useState<TagSearchResult[]>([])
  const [tagTypes, setTagTypes] = useState<string[]>([])
  const [newTagValue, setNewTagValue] = useState('')
  const [newTagType, setNewTagType] = useState('')
  const [showCreateTag, setShowCreateTag] = useState(false)

  const fetchProduct = useCallback(async () => {
    try {
      setLoading(true)
      setError('')

      const data = await productsApi.getProduct(productId)
      setProduct(data)
    } catch (err) {
      setError(getErrorMessage(err, t('product:errors.loadFailed')))
    } finally {
      setLoading(false)
    }
  }, [productId, t])

  useEffect(() => {
    fetchProduct()
  }, [productId, fetchProduct])

  const searchTags = useCallback(async (query: string) => {
    if (query.trim().length < 1) {
      setTagResults([])
      return
    }
    try {
      const results = await tagsApi.search(query)
      // Filter out tags already on the product
      const existingIds = new Set(product?.tags?.map(t => t.id) || [])
      setTagResults(results.filter(r => !existingIds.has(r.id)))
    } catch {
      setTagResults([])
    }
  }, [product?.tags])

  const handleAddTag = async (tagId: string) => {
    try {
      await tagsApi.addTagToProduct(tagId, productId)
      await fetchProduct()
      setTagSearch('')
      setTagResults([])
      setShowTagSelector(false)
    } catch {
      // error handled silently
    }
  }

  const handleRemoveTag = async (tagId: string) => {
    try {
      await tagsApi.removeTagFromProduct(tagId, productId)
      await fetchProduct()
    } catch {
      // error handled silently
    }
  }

  const handleCreateTag = async () => {
    if (!newTagValue.trim() || !newTagType) return
    try {
      const result = await tagsApi.createTag({ value: newTagValue.trim(), type: newTagType })
      // The result has the new tag's id
      if (result && (result as { id?: string }).id) {
        await tagsApi.addTagToProduct((result as { id: string }).id, productId)
        await fetchProduct()
      }
      setNewTagValue('')
      setNewTagType('')
      setShowCreateTag(false)
      setShowTagSelector(false)
    } catch {
      // error handled silently
    }
  }

  const openTagSelector = async () => {
    setShowTagSelector(true)
    if (tagTypes.length === 0) {
      try {
        const types = await tagsApi.getTypes()
        setTagTypes(types)
        if (types.length > 0) setNewTagType(types[0])
      } catch {
        // use defaults
      }
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  if (error || !product) {
    return <ErrorAlert message={error || t('product:errors.notFound')} onRetry={fetchProduct} />
  }

  return (
    <div className="product-page">
      <div className="breadcrumb">
        <span onClick={onBack} className="breadcrumb-link">{t('common:navigation.dashboard')}</span>
        <span className="breadcrumb-separator">›</span>
        <span>{product.name}</span>
      </div>

      <div className="product-header">
        <h2>{product.name}</h2>
        {(product.brand || product.unit) && (
          <div className="product-meta">
            {product.brand && <span className="meta-item">{t('product:fields.brand')}: {product.brand}</span>}
            {product.unit && <span className="meta-item">{t('product:fields.unit')}: {product.unit}</span>}
          </div>
        )}
      </div>

      <div className="product-tags-section">
        <div className="tags-header">
          <h4>{t('product:tags.title')}</h4>
          {!showTagSelector && (
            <button className="btn btn-sm" onClick={openTagSelector}>
              + {t('product:tags.addTag')}
            </button>
          )}
        </div>

        <div className="tags-list">
          {(product.tags || []).map((tag) => (
            <span
              key={tag.id}
              className={`tag-chip tag-type-${tag.type}`}
            >
              <span className="tag-chip-text" onClick={() => navigate(`/tags/${tag.id}`)}>
                {tag.value}
              </span>
              <button
                className="tag-chip-remove"
                onClick={() => handleRemoveTag(tag.id)}
                title={t('product:tags.removeTag')}
              >
                &times;
              </button>
            </span>
          ))}
          {(!product.tags || product.tags.length === 0) && !showTagSelector && (
            <span className="no-tags-hint">{t('product:tags.noTags')}</span>
          )}
        </div>

        {showTagSelector && (
          <div className="tag-selector">
            <input
              type="text"
              className="form-input"
              placeholder={t('product:tags.searchPlaceholder')}
              value={tagSearch}
              onChange={(e) => {
                setTagSearch(e.target.value)
                searchTags(e.target.value)
              }}
              autoFocus
            />
            {tagResults.length > 0 && (
              <div className="tag-results">
                {tagResults.map((tag) => (
                  <div
                    key={tag.id}
                    className="tag-result-item"
                    onClick={() => handleAddTag(tag.id)}
                  >
                    <span className="tag-result-value">{tag.value}</span>
                    <span className={`tag-type-badge tag-type-${tag.type}`}>{t(`product:tags.types.${tag.type}`, tag.type)}</span>
                    <span className="tag-result-count">{tag.product_count}</span>
                  </div>
                ))}
              </div>
            )}

            {!showCreateTag && (
              <button className="btn btn-sm tag-create-btn" onClick={() => setShowCreateTag(true)}>
                {t('product:tags.createNew')}
              </button>
            )}

            {showCreateTag && (
              <div className="tag-create-form">
                <input
                  type="text"
                  className="form-input"
                  placeholder={t('product:tags.newValuePlaceholder')}
                  value={newTagValue}
                  onChange={(e) => setNewTagValue(e.target.value)}
                />
                <select
                  className="form-input"
                  value={newTagType}
                  onChange={(e) => setNewTagType(e.target.value)}
                >
                  {tagTypes.map((type) => (
                    <option key={type} value={type}>
                      {t(`product:tags.types.${type}`, type)}
                    </option>
                  ))}
                </select>
                <div className="tag-create-actions">
                  <button className="btn btn-primary btn-sm" onClick={handleCreateTag} disabled={!newTagValue.trim() || !newTagType}>
                    {t('common:actions.create')}
                  </button>
                  <button className="btn btn-sm" onClick={() => { setShowCreateTag(false); setShowTagSelector(false) }}>
                    {t('common:actions.cancel')}
                  </button>
                </div>
              </div>
            )}

            {!showCreateTag && (
              <button className="btn btn-sm tag-cancel-btn" onClick={() => { setShowTagSelector(false); setTagSearch(''); setTagResults([]) }}>
                {t('common:actions.cancel')}
              </button>
            )}
          </div>
        )}
      </div>

      {product.stores.length === 0 && (
        <div className="empty-state">
          <p>{t('product:emptyStates.noStoreInfo')}</p>
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
                        <span className="price-label">{t('product:priceHistory.currentPrice')}:</span>
                        <span className="price-value">{store.current_price.toFixed(2)} RSD</span>
                      </div>
                    )}
                  </div>

                  {allPrices.length === 0 ? (
                    <p className="no-price-data">{t('product:priceHistory.noHistory')}</p>
                  ) : (
                    <div className="price-summary">
                      {minPrice !== null && (
                        <div className="price-stat">
                          <span className="price-label">{t('product:priceHistory.lowest')}</span>
                          <span className="price-value price-min">{minPrice.toFixed(2)} RSD</span>
                        </div>
                      )}
                      {avgPrice !== null && (
                        <div className="price-stat">
                          <span className="price-label">{t('product:priceHistory.average')}</span>
                          <span className="price-value">{avgPrice.toFixed(2)} RSD</span>
                        </div>
                      )}
                      {maxPrice !== null && maxPrice !== minPrice && (
                        <div className="price-stat">
                          <span className="price-label">{t('product:priceHistory.highest')}</span>
                          <span className="price-value price-max">{maxPrice.toFixed(2)} RSD</span>
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
