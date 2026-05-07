import { useState, useEffect, useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Store, UserPlus, X } from 'lucide-react'
import '../styles/pages/StorePage.css'
import LoadingSpinner from '../components/common/LoadingSpinner'
import '../styles/components/LoadingSpinner.css'
import ErrorAlert from '../components/common/ErrorAlert'
import RunCard from '../components/RunCard'
import NewProductPopup from '../components/popups/NewProductPopup'
import { API_BASE_URL } from '../config'
import { getErrorMessage } from '../utils/errorHandling'
import { groupsApi, type Group } from '../api/groups'
import { useMyFollowingGroups, useFollowSeller, useUnfollowSeller } from '../hooks/queries/useSellers'
import { sellerKeys } from '../hooks/queries/useSellers'
import { useQueryClient } from '@tanstack/react-query'
import { logger } from '../utils/logger'

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
  leader_is_removed?: boolean
  planned_on: string | null
  planning_at: string | null
  active_at: string | null
  confirmed_at: string | null
  shopping_at: string | null
  adjusting_at: string | null
  distributing_at: string | null
  completed_at: string | null
  cancelled_at: string | null
}

interface SellerInfo {
  id: string
  display_name: string
  description: string | null
  is_joining_allowed: boolean
}

interface StorePageData {
  store: {
    id: string
    name: string
  }
  products: Product[]
  active_runs: ActiveRun[]
  seller: SellerInfo | null
}

interface StorePageProps {
  storeId: string
  onBack: () => void
}

function StorePage({ storeId, onBack }: StorePageProps) {
  const { t } = useTranslation(['common', 'product', 'store', 'seller'])
  const [data, setData] = useState<StorePageData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showNewProductPopup, setShowNewProductPopup] = useState(false)
  const [showFollowForm, setShowFollowForm] = useState(false)
  const [allGroups, setAllGroups] = useState<Group[]>([])
  const [selectedGroupId, setSelectedGroupId] = useState('')
  const [followError, setFollowError] = useState('')

  const sellerId = data?.seller?.id
  const { data: followingGroups = [], refetch: refetchFollowing } = useMyFollowingGroups(sellerId)
  const followMutation = useFollowSeller()
  const unfollowMutation = useUnfollowSeller()
  const queryClient = useQueryClient()

  const fetchStoreData = useCallback(async () => {
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
  }, [storeId, t])

  useEffect(() => {
    fetchStoreData()
  }, [storeId, fetchStoreData])

  const followingGroupIds = useMemo(
    () => new Set(followingGroups.map(f => f.group_id)),
    [followingGroups]
  )

  const availableGroups = useMemo(
    () => allGroups.filter(g => !followingGroupIds.has(g.id)),
    [allGroups, followingGroupIds]
  )

  const handleShowFollowForm = async () => {
    try {
      const myGroups = await groupsApi.getMyGroups()
      setAllGroups(myGroups)
      setShowFollowForm(true)
      const available = myGroups.filter(g => !followingGroupIds.has(g.id))
      if (available.length > 0) setSelectedGroupId(available[0].id)
    } catch (err) {
      logger.error('Failed to load groups:', err)
    }
  }

  const handleFollow = () => {
    if (!sellerId || !selectedGroupId) return
    setFollowError('')

    followMutation.mutate(
      { sellerId, groupId: selectedGroupId },
      {
        onSuccess: () => {
          setShowFollowForm(false)
          refetchFollowing()
          queryClient.invalidateQueries({ queryKey: sellerKeys.all })
        },
        onError: (err) => {
          setFollowError(getErrorMessage(err, t('seller:join.errors.followFailed')))
        },
      }
    )
  }

  const handleUnfollow = (groupId: string) => {
    if (!sellerId) return
    unfollowMutation.mutate(
      { sellerId, groupId },
      {
        onSuccess: () => {
          refetchFollowing()
          queryClient.invalidateQueries({ queryKey: sellerKeys.all })
        },
      }
    )
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
        <h1>{data.seller ? <><Store size={24} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} />{data.seller.display_name}</> : data.store.name}</h1>
        {data.seller?.description && (
          <p className="seller-description">{data.seller.description}</p>
        )}
      </div>

      {/* Seller following section */}
      {data.seller && (
        <section className="seller-following-section">
          {followingGroups.length > 0 && (
            <div className="following-groups">
              <h3>{t('seller:public.followingWith')}</h3>
              {followingGroups.map(f => (
                <div key={f.id} className="following-group-item">
                  <span>{f.group_name}</span>
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => handleUnfollow(f.group_id)}
                    disabled={unfollowMutation.isPending}
                  >
                    <X size={14} />
                    {t('seller:followers.unfollow')}
                  </button>
                </div>
              ))}
            </div>
          )}

          {data.seller.is_joining_allowed && !showFollowForm && (
            <button className="btn btn-primary" onClick={handleShowFollowForm} style={{ marginTop: '0.5rem' }}>
              <UserPlus size={16} style={{ marginRight: '0.35rem' }} />
              {t('seller:public.followWithGroup')}
            </button>
          )}

          {showFollowForm && (
            <div className="follow-form" style={{ marginTop: '0.5rem' }}>
              {availableGroups.length === 0 ? (
                <p className="text-secondary">{t('seller:public.allGroupsFollowing')}</p>
              ) : (
                <>
                  <div className="form-group">
                    <select
                      className="form-input"
                      value={selectedGroupId}
                      onChange={(e) => setSelectedGroupId(e.target.value)}
                    >
                      {availableGroups.map(g => (
                        <option key={g.id} value={g.id}>{g.name}</option>
                      ))}
                    </select>
                  </div>
                  {followError && <div className="alert alert-error">{followError}</div>}
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      className="btn btn-primary"
                      onClick={handleFollow}
                      disabled={followMutation.isPending || !selectedGroupId}
                    >
                      {followMutation.isPending ? t('seller:join.following') : t('seller:join.follow')}
                    </button>
                    <button className="btn btn-secondary" onClick={() => setShowFollowForm(false)}>
                      {t('common:buttons.cancel')}
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      )}

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
