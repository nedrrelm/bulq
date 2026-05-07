import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { tagsApi } from '../api'
import type { TagDetail } from '../api/tags'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorAlert from '../components/common/ErrorAlert'
import { getErrorMessage } from '../utils/errorHandling'
import '../styles/pages/TagPage.css'

interface TagPageProps {
  tagId: string
  onBack: () => void
}

export default function TagPage({ tagId, onBack }: TagPageProps) {
  const { t } = useTranslation(['common', 'product'])
  const navigate = useNavigate()
  const [tag, setTag] = useState<TagDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchTag = useCallback(async () => {
    try {
      setLoading(true)
      setError('')
      const data = await tagsApi.getTag(tagId)
      setTag(data)
    } catch (err) {
      setError(getErrorMessage(err, t('product:tags.errors.loadFailed')))
    } finally {
      setLoading(false)
    }
  }, [tagId, t])

  useEffect(() => {
    fetchTag()
  }, [tagId, fetchTag])

  if (loading) {
    return <LoadingSpinner />
  }

  if (error || !tag) {
    return <ErrorAlert message={error || t('product:tags.errors.notFound')} onRetry={fetchTag} />
  }

  return (
    <div className="tag-page">
      <div className="breadcrumb">
        <span onClick={onBack} className="breadcrumb-link">{t('common:navigation.dashboard')}</span>
        <span className="breadcrumb-separator">&rsaquo;</span>
        <span>{tag.value}</span>
      </div>

      <div className="tag-header">
        <h2>{tag.value}</h2>
        <span className={`tag-type-badge tag-type-${tag.type}`}>{t(`product:tags.types.${tag.type}`, tag.type)}</span>
        {tag.verified && <span className="tag-verified-badge">{t('admin:actions.verify')}</span>}
      </div>

      <div className="tag-products-section">
        <h3>{t('product:tags.productsWithTag', { count: tag.product_count })}</h3>

        {tag.products.length === 0 ? (
          <div className="empty-state">
            <p>{t('product:tags.noProducts')}</p>
          </div>
        ) : (
          <div className="tag-products-list">
            {tag.products.map((product) => (
              <div
                key={product.id}
                className="tag-product-card card"
                onClick={() => navigate(`/products/${product.id}`)}
              >
                <div className="tag-product-info">
                  <strong>{product.name}</strong>
                  {product.brand && <span className="tag-product-brand">{product.brand}</span>}
                  {product.unit && <span className="tag-product-unit">{product.unit}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
