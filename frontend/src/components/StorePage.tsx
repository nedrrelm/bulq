import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import '../styles/components/StorePage.css'
import LoadingSpinner from './LoadingSpinner'
import '../styles/components/LoadingSpinner.css'
import ErrorAlert from './ErrorAlert'
import RunCard from './RunCard'
import NewProductPopup from './NewProductPopup'
import { API_BASE_URL } from '../config'
import { getErrorMessage } from '../utils/errorHandling'

interface Product {
  id: string
  name: string
  brand: string | null
  unit: string | null
  current_price: string | null
}

interface ActiveRun {
  id: string
  state: string
  group_id: string
  group_name: string
  store_name: string
  leader_name: string
  planned_on: string | null
}

interface StorePageData {
  store: {
    id: string
    name: string
  }
  products: Product[]
  active_runs: ActiveRun[]
}

interface StorePageProps {
  storeId: string
  onBack: () => void
}

function StorePage({ storeId, onBack }: StorePageProps) {
  const { t } = useTranslation(['common', 'product', 'store'])
  const [data, setData] = useState<StorePageData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showNewProductPopup, setShowNewProductPopup] = useState(false)

  useEffect(() => {
    fetchStoreData()
  }, [storeId])

  const fetchStoreData = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE_URL}/stores/${storeId}`, {
        credentials: 'include'
      })

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error(t('store:errors.notFound'))
        }
        throw new Error(t('store:errors.loadFailed'))
      }

      const storeData = await response.json()
      setData(storeData)
    } catch (err) {
      setError(getErrorMessage(err, t('common:errors.generic')))
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingSpinner />
  }

  if (error) {
    return (
      <div className="store-page">
        <button className="btn btn-secondary back-btn" onClick={onBack}>
          {t('common:actions.back')}
        </button>
        <ErrorAlert message={error} />
      </div>
    )
  }

  if (!data) {
    return null
  }

  return (
    <div className="store-page">
      <button className="btn btn-secondary back-btn" onClick={onBack}>
        {t('common:actions.back')}
      </button>

      <div className="store-header">
        <h1>{data.store.name}</h1>
      </div>

      {data.active_runs.length > 0 && (
        <section className="active-runs-section">
          <h2>{t('store:sections.activeRuns', { count: data.active_runs.length })}</h2>
          <div className="active-runs-list">
            {data.active_runs.map(run => (
              <RunCard key={run.id} run={run} showGroupName={true} />
            ))}
          </div>
        </section>
      )}

      <section className="products-section">
        <div className="section-header">
          <h2>{t('store:sections.products')}</h2>
          <button
            className="btn btn-primary"
            onClick={() => setShowNewProductPopup(true)}
          >
            {t('product:actions.addNew')}
          </button>
        </div>
        {data.products.length === 0 ? (
          <div className="empty-state">
            <p>{t('store:emptyStates.noProducts')}</p>
            <p className="empty-state-hint">
              {t('store:emptyStates.noProductsHint')}
            </p>
          </div>
        ) : (
          <div className="products-list">
            {data.products.map(product => (
              <Link
                key={product.id}
                to={`/products/${product.id}`}
                className="product-card card"
              >
                <div className="product-info">
                  <div className="product-name">{product.name}</div>
                  {product.brand && (
                    <div className="product-brand">{product.brand}</div>
                  )}
                  <div className="product-details">
                    {product.unit && <span className="product-unit">{product.unit}</span>}
                    {product.current_price && (
                      <span className="product-price">≈ ${product.current_price}</span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {showNewProductPopup && (
        <NewProductPopup
          initialStoreId={storeId}
          onClose={() => setShowNewProductPopup(false)}
          onSuccess={() => {
            setShowNewProductPopup(false)
            fetchStoreData()
          }}
        />
      )}
    </div>
  )
}

export default StorePage
