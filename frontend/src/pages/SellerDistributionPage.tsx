import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, CheckCircle, Package } from 'lucide-react'
import { salesApi } from '../api/sales'
import { getErrorMessage } from '../utils/errorHandling'
import { logger } from '../utils/logger'
import '../styles/pages/SellerDashboardPage.css'

interface DistributionGroup {
  item_id: string
  run_id: string
  group_id: string
  group_name: string
  leader_name: string
  quantity: number
  is_handed_over: boolean
  handed_over_at: string | null
}

interface DistributionProduct {
  product_id: string
  product_name: string
  product_unit: string | null
  total_quantity: number
  groups: DistributionGroup[]
}

interface DistributionData {
  sale_id: string
  state: string
  products: DistributionProduct[]
  total_items: number
  handed_over_count: number
}

export default function SellerDistributionPage() {
  const { t } = useTranslation(['seller'])
  const { saleId } = useParams<{ saleId: string }>()
  const navigate = useNavigate()

  const [data, setData] = useState<DistributionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toggling, setToggling] = useState<string | null>(null)

  const fetchDistribution = useCallback(async () => {
    if (!saleId) return
    try {
      setLoading(true)
      const result = await salesApi.getDistribution(saleId) as DistributionData
      setData(result)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load distribution'))
    } finally {
      setLoading(false)
    }
  }, [saleId])

  useEffect(() => {
    fetchDistribution()
  }, [fetchDistribution])

  const handleToggleHandover = async (itemId: string) => {
    if (!saleId) return
    setToggling(itemId)
    try {
      const result = await salesApi.toggleHandover(saleId, itemId) as DistributionData
      setData(result)
    } catch (err) {
      logger.error('Failed to toggle handover:', err)
    } finally {
      setToggling(null)
    }
  }

  const handleComplete = async () => {
    if (!saleId) return
    try {
      await salesApi.completeSale(saleId)
      navigate(`/seller/sale/${saleId}`)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to complete sale'))
    }
  }

  if (loading) return <div className="seller-page"><p>Loading...</p></div>
  if (error) return <div className="seller-page"><div className="alert alert-error">{error}</div></div>
  if (!data) return null

  const allHandedOver = data.total_items > 0 && data.handed_over_count === data.total_items
  const progress = data.total_items > 0 ? Math.round((data.handed_over_count / data.total_items) * 100) : 0

  return (
    <div className="seller-page">
      <button className="btn btn-secondary" onClick={() => navigate(`/seller/sale/${saleId}`)} style={{ marginBottom: '1rem' }}>
        <ArrowLeft size={16} /> {t('seller:distribution.backToSale')}
      </button>

      <h1>{t('seller:distribution.title')}</h1>

      {/* Progress */}
      <div className="card" style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong>{t('seller:distribution.progress')}</strong>
            <span style={{ marginLeft: '0.5rem', color: 'var(--color-text-secondary)' }}>
              {data.handed_over_count} / {data.total_items} ({progress}%)
            </span>
          </div>
          {allHandedOver && data.state === 'distributing' && (
            <button className="btn btn-success" onClick={handleComplete}>
              <CheckCircle size={16} /> {t('seller:distribution.completeSale')}
            </button>
          )}
        </div>
        <div style={{ marginTop: '0.5rem', background: 'var(--color-bg-secondary)', borderRadius: '4px', height: '8px' }}>
          <div style={{ width: `${progress}%`, background: 'var(--color-primary)', borderRadius: '4px', height: '100%', transition: 'width 0.3s' }} />
        </div>
      </div>

      {/* Per-product breakdown */}
      {data.products.map((product) => (
        <div key={product.product_id} className="card" style={{ marginBottom: '0.75rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <h3 style={{ margin: 0 }}>
              <Package size={16} style={{ marginRight: '0.35rem', verticalAlign: 'middle' }} />
              {product.product_name}
            </h3>
            <span style={{ color: 'var(--color-text-secondary)' }}>
              {product.total_quantity}{product.product_unit ? ` ${product.product_unit}` : ''}
            </span>
          </div>

          {product.groups.map((group) => (
            <div
              key={group.item_id}
              className="sale-product-item"
              style={{ cursor: 'pointer' }}
              onClick={() => handleToggleHandover(group.item_id)}
            >
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', flex: 1 }}>
                <input
                  type="checkbox"
                  checked={group.is_handed_over}
                  onChange={() => {}}
                  disabled={toggling === group.item_id}
                  style={{ width: '18px', height: '18px' }}
                />
                <div>
                  <strong>{group.group_name}</strong>
                  <span style={{ color: 'var(--color-text-secondary)', marginLeft: '0.5rem', fontSize: '0.85rem' }}>
                    ({group.leader_name})
                  </span>
                </div>
              </label>
              <span style={{ fontWeight: 500 }}>
                {group.quantity}{product.product_unit ? ` ${product.product_unit}` : ''}
              </span>
            </div>
          ))}
        </div>
      ))}

      {data.products.length === 0 && (
        <div className="card">
          <div className="empty-state">
            <p>{t('seller:distribution.noItems')}</p>
          </div>
        </div>
      )}
    </div>
  )
}
