import { useTranslation } from 'react-i18next'
import type { RunDetail } from '../api'
import type { DistributionUser } from '../schemas/distribution'
import DownloadRunStateButton from './DownloadRunStateButton'

interface EnrichedDistributionProduct {
  bid_id: string
  product_id: string
  product_name: string
  product_unit: string | null
  requested_quantity: number
  distributed_quantity: number
  price_per_unit: string
  subtotal: string
  is_picked_up: boolean
  remaining_total: number
  distributed_total: number
}

export interface EnrichedDistributionUser {
  user_id: string
  user_name: string
  products: EnrichedDistributionProduct[]
  total_cost: string
  all_picked_up: boolean
}

export interface BidBreakdownUser {
  user_id: string
  user_name: string
  products: {
    product_id: string
    product_name: string
    product_unit: string | null
    quantity: number
    price_per_unit: number
    subtotal: number
  }[]
  total_cost: string
  fee_share: string
}

interface RunDistributionSectionProps {
  run: RunDetail
  runId: string
  shouldFetchDistribution: boolean
  distributionUsers: EnrichedDistributionUser[]
  userBreakdownFromBids: BidBreakdownUser[]
  expandedUserId: string | null
  onToggleExpand: (userId: string) => void
  allPickedUp: boolean
  isLeaderOrHelper: boolean
  onMarkPickedUp: (bidId: string) => void
  onMarkAllPickedUp: (user: DistributionUser) => void
  onCompleteRun: () => void
  markPickedUpPending: boolean
  completeDistributionPending: boolean
}

export default function RunDistributionSection({
  run,
  runId,
  shouldFetchDistribution,
  distributionUsers,
  userBreakdownFromBids,
  expandedUserId,
  onToggleExpand,
  allPickedUp,
  isLeaderOrHelper,
  onMarkPickedUp,
  onMarkAllPickedUp,
  onCompleteRun,
  markPickedUpPending,
  completeDistributionPending,
}: RunDistributionSectionProps) {
  const { t } = useTranslation(['common', 'run'])

  if (run.state === 'cancelled') return null

  return (
    <div className="distribution-section">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3>
          {shouldFetchDistribution
            ? t('run:labels.distribution')
            : t('run:labels.userBreakdown')}
          {!shouldFetchDistribution && (
            <span className="text-sm text-secondary ml-sm">
              ({t('run:labels.estimated')})
            </span>
          )}
        </h3>
        {shouldFetchDistribution && (run.current_user_is_leader || run.current_user_is_helper) && (
          <DownloadRunStateButton
            runId={runId}
            storeName={run.store_name}
            className="btn btn-secondary"
          />
        )}
      </div>

      {shouldFetchDistribution ? (
        <>
          {distributionUsers.length === 0 ? (
            <div className="empty-state">
              <p>{t('run:empty.noItemsToDistribute')}</p>
            </div>
          ) : (
            <div className="distribution-list">
              {distributionUsers.map(user => (
                <div key={user.user_id} className={`user-card ${user.all_picked_up ? 'completed' : ''}`}>
                  <div
                    className="user-header"
                    onClick={() => onToggleExpand(user.user_id)}
                  >
                    <div className="user-info">
                      <span className="user-name">{user.user_name}</span>
                      <span className="user-total">{user.total_cost} RSD</span>
                    </div>
                    <div className="user-actions">
                      {user.all_picked_up && <span className="pickup-badge">{t('run:labels.pickedUp')}</span>}
                      <span className="expand-icon">{expandedUserId === user.user_id ? '▼' : '▶'}</span>
                    </div>
                  </div>

                  {expandedUserId === user.user_id && (
                    <div className="user-products">
                      <div className="user-products-header">
                        {!user.all_picked_up && isLeaderOrHelper && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              onMarkAllPickedUp(user as unknown as DistributionUser)
                            }}
                            className="mark-all-button"
                            disabled={markPickedUpPending}
                          >
                            {markPickedUpPending ? t('run:labels.updating') : t('run:actions.markAllPickedUp')}
                          </button>
                        )}
                      </div>
                      {user.products
                        .sort((a, b) => a.product_name.localeCompare(b.product_name))
                        .map(product => {
                          const productData = run.products.find(p => p.id === product.product_id)
                          const isUnbought = (run.state === 'distributing' || run.state === 'completed') &&
                                             productData &&
                                             (productData.purchased_quantity === null || productData.purchased_quantity === 0)

                          return (
                            <div key={product.bid_id} className={`product-item ${product.is_picked_up ? 'picked-up' : ''} ${isUnbought ? 'unbought' : ''}`}>
                              <div className="product-info">
                                <div className="product-name">
                                  {product.product_name}
                                  {product.distributed_quantity < product.requested_quantity && (
                                    <span className="shortage-badge" title={t('run:labels.quantityReducedTooltip')}>⚠️</span>
                                  )}
                                </div>
                                <div className="product-details">
                                  <span>{t('run:labels.requested')}: {product.requested_quantity}{product.product_unit ? ` ${product.product_unit}` : ''}</span>
                                  <span>{t('run:labels.allocated')}: {product.distributed_quantity}{product.product_unit ? ` ${product.product_unit}` : ''} <span className="remaining-info">({product.remaining_total}/{product.distributed_total} {t('run:labels.left')})</span></span>
                                  <span>@{product.price_per_unit} RSD</span>
                                  <span className="product-subtotal">{product.subtotal} RSD</span>
                                </div>
                              </div>
                              {isLeaderOrHelper && (
                                <button
                                  onClick={() => onMarkPickedUp(product.bid_id)}
                                  disabled={product.is_picked_up || markPickedUpPending}
                                  className={`pickup-button ${product.is_picked_up ? 'picked-up' : ''}`}
                                >
                                  {markPickedUpPending ? t('run:labels.updating') : product.is_picked_up ? t('run:labels.pickedUp') : t('run:actions.markPickedUp')}
                                </button>
                              )}
                            </div>
                          )
                        })}
                      {user.fee_share && parseFloat(user.fee_share) > 0 && (
                        <div className="product-item" style={{ borderTop: '1px dashed var(--color-border, #e5e7eb)', paddingTop: '0.5rem' }}>
                          <div className="product-info">
                            <div className="product-name" style={{ fontStyle: 'italic' }}>{t('run:labels.leaderFeeShare')}</div>
                            <div className="product-details">
                              <span className="product-subtotal">{user.fee_share} RSD</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {allPickedUp && isLeaderOrHelper && run.state === 'distributing' && (
            <div className="complete-section">
              <button
                onClick={onCompleteRun}
                className="complete-button"
                disabled={completeDistributionPending}
              >
                {completeDistributionPending ? t('run:labels.completing') : t('run:actions.completeRun')}
              </button>
            </div>
          )}
        </>
      ) : (
        userBreakdownFromBids.length === 0 ? (
          <div className="empty-state">
            <p>{t('run:empty.noBidsYet')}</p>
          </div>
        ) : (
          <div className="distribution-list">
            {userBreakdownFromBids.map(user => (
              <div key={user.user_id} className="user-card">
                <div
                  className="user-header"
                  onClick={() => onToggleExpand(user.user_id)}
                >
                  <div className="user-info">
                    <span className="user-name">{user.user_name}</span>
                    <span className="user-total">{user.total_cost} RSD</span>
                  </div>
                  <div className="user-actions">
                    <span className="expand-icon">{expandedUserId === user.user_id ? '▼' : '▶'}</span>
                  </div>
                </div>

                {expandedUserId === user.user_id && (
                  <div className="user-products">
                    {user.products
                      .sort((a, b) => a.product_name.localeCompare(b.product_name))
                      .map(product => {
                        const productData = run.products.find(p => p.id === product.product_id)
                        const isUnbought = (run.state === 'adjusting' || run.state === 'distributing' || run.state === 'completed') &&
                                           productData &&
                                           (productData.purchased_quantity === null || productData.purchased_quantity === 0)

                        return (
                          <div key={product.product_id} className={`product-item ${isUnbought ? 'unbought' : ''}`}>
                            <div className="product-info">
                              <div className="product-name">
                                {product.product_name}
                              </div>
                              <div className="product-details">
                                <span>{t('run:labels.quantity')}: {product.quantity}{product.product_unit ? ` ${product.product_unit}` : ''}</span>
                                {product.price_per_unit > 0 && (
                                  <>
                                    <span>@{product.price_per_unit} RSD</span>
                                    <span className="product-subtotal">{product.subtotal.toFixed(2)} RSD</span>
                                  </>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                      {user.fee_share && parseFloat(user.fee_share) > 0 && (
                        <div className="product-item" style={{ borderTop: '1px dashed var(--color-border, #e5e7eb)', paddingTop: '0.5rem' }}>
                          <div className="product-info">
                            <div className="product-name" style={{ fontStyle: 'italic' }}>{t('run:labels.leaderFeeShare')}</div>
                            <div className="product-details">
                              <span className="product-subtotal">{user.fee_share} RSD</span>
                            </div>
                          </div>
                        </div>
                      )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
