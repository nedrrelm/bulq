import { useState } from 'react'
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
  fee_share?: string
  all_picked_up: boolean
}

export interface EnrichedDistributionGroup {
  id: string
  name: string
  is_default: boolean
  is_done: boolean
  sort_order: number
  users: EnrichedDistributionUser[]
  total_cost: string
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
  distributionGroups: EnrichedDistributionGroup[]
  distributionUsers: EnrichedDistributionUser[]
  userBreakdownFromBids: BidBreakdownUser[]
  expandedUserId: string | null
  onToggleExpand: (userId: string) => void
  allPickedUp: boolean
  isLeaderOrHelper: boolean
  onMarkPickedUp: (bidId: string) => void
  onMarkAllPickedUp: (user: DistributionUser) => void
  onCompleteRun: () => void
  onCreateGroup: () => void
  onDeleteGroup: (groupId: string) => void
  onAssignUserToGroup: (groupId: string, userId: string) => void
  onMarkGroupDone: (groupId: string) => void
  markPickedUpPending: boolean
  completeDistributionPending: boolean
}

function UserCard({
  user,
  run,
  expandedUserId,
  onToggleExpand,
  isLeaderOrHelper,
  onMarkPickedUp,
  onMarkAllPickedUp,
  markPickedUpPending,
  groups,
  onAssignUserToGroup,
}: {
  user: EnrichedDistributionUser
  run: RunDetail
  expandedUserId: string | null
  onToggleExpand: (userId: string) => void
  isLeaderOrHelper: boolean
  onMarkPickedUp: (bidId: string) => void
  onMarkAllPickedUp: (user: DistributionUser) => void
  markPickedUpPending: boolean
  groups?: EnrichedDistributionGroup[]
  onAssignUserToGroup?: (groupId: string, userId: string) => void
}) {
  const { t } = useTranslation(['common', 'run'])
  const [showMoveMenu, setShowMoveMenu] = useState(false)
  const hasMultipleGroups = groups && groups.length > 1

  return (
    <div className={`user-card ${user.all_picked_up ? 'completed' : ''}`}>
      <div
        className="user-header"
        onClick={() => onToggleExpand(user.user_id)}
      >
        <div className="user-info">
          <span className="user-name">
            {user.user_name}
            {hasMultipleGroups && isLeaderOrHelper && run.state === 'distributing' && (
              <span className="move-user-wrapper" onClick={e => e.stopPropagation()}>
                <button
                  className="move-user-button"
                  onClick={() => setShowMoveMenu(!showMoveMenu)}
                  title={t('run:distributionGroups.moveTo')}
                >
                  ↔
                </button>
                {showMoveMenu && (
                  <div className="move-user-menu">
                    {groups.map(g => (
                      <button
                        key={g.id}
                        className="move-user-menu-item"
                        onClick={() => {
                          onAssignUserToGroup?.(g.id, user.user_id)
                          setShowMoveMenu(false)
                        }}
                      >
                        {t('run:distributionGroups.groupLabel', { name: g.name })}
                      </button>
                    ))}
                  </div>
                )}
              </span>
            )}
          </span>
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
  )
}

export default function RunDistributionSection({
  run,
  runId,
  shouldFetchDistribution,
  distributionGroups,
  distributionUsers,
  userBreakdownFromBids,
  expandedUserId,
  onToggleExpand,
  allPickedUp,
  isLeaderOrHelper,
  onMarkPickedUp,
  onMarkAllPickedUp,
  onCompleteRun,
  onCreateGroup,
  onDeleteGroup,
  onAssignUserToGroup,
  onMarkGroupDone,
  markPickedUpPending,
  completeDistributionPending,
}: RunDistributionSectionProps) {
  const { t } = useTranslation(['common', 'run'])
  const [collapsedGroupIds, setCollapsedGroupIds] = useState<Set<string>>(new Set())

  if (run.state === 'cancelled') return null

  const toggleGroup = (groupId: string) => {
    setCollapsedGroupIds(prev => {
      const next = new Set(prev)
      if (next.has(groupId)) {
        next.delete(groupId)
      } else {
        next.add(groupId)
      }
      return next
    })
  }

  const hasMultipleGroups = distributionGroups.length > 1
  // For single group, just use its users directly
  const singleGroupUsers = !hasMultipleGroups && distributionGroups.length === 1
    ? distributionGroups[0].users
    : []

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
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            {run.state === 'distributing' && run.current_user_is_leader && (
              <button
                onClick={onCreateGroup}
                className="btn btn-secondary btn-sm"
                title={t('run:distributionGroups.addGroup')}
              >
                + {t('run:distributionGroups.addGroup')}
              </button>
            )}
            <DownloadRunStateButton
              runId={runId}
              storeName={run.store_name}
              className="btn btn-secondary"
            />
          </div>
        )}
      </div>

      {shouldFetchDistribution ? (
        <>
          {distributionUsers.length === 0 ? (
            <div className="empty-state">
              <p>{t('run:empty.noItemsToDistribute')}</p>
            </div>
          ) : hasMultipleGroups ? (
            /* Multiple groups: show collapsible group sections */
            <div className="distribution-list">
              {distributionGroups.map(group => {
                const isExpanded = !collapsedGroupIds.has(group.id)

                // Compute per-product totals for this group
                const groupProductTotals = new Map<string, { productId: string, name: string, unit: string | null, quantity: number, cost: number }>()
                for (const user of group.users) {
                  for (const p of user.products) {
                    const existing = groupProductTotals.get(p.product_id)
                    if (existing) {
                      existing.quantity += p.distributed_quantity
                      existing.cost += parseFloat(p.subtotal)
                    } else {
                      groupProductTotals.set(p.product_id, {
                        productId: p.product_id,
                        name: p.product_name,
                        unit: p.product_unit,
                        quantity: p.distributed_quantity,
                        cost: parseFloat(p.subtotal),
                      })
                    }
                  }
                }
                const sortedProducts = [...groupProductTotals.values()].sort((a, b) => a.name.localeCompare(b.name))

                return (
                  <div key={group.id} className={`distribution-group ${group.is_done ? 'done' : ''}`}>
                    <div
                      className="distribution-group-header"
                      onClick={() => toggleGroup(group.id)}
                    >
                      <div className="distribution-group-info">
                        <span className="distribution-group-name">
                          {t('run:distributionGroups.groupLabel', { name: group.name })}
                        </span>
                        <span className="distribution-group-total">{group.total_cost} RSD</span>
                      </div>
                      <div className="distribution-group-actions">
                        {group.is_done && (
                          <span className="pickup-badge">{t('run:distributionGroups.groupDone')}</span>
                        )}
                        {!group.is_done && isLeaderOrHelper && run.state === 'distributing' && (
                          <button
                            className="btn btn-sm btn-success"
                            onClick={(e) => {
                              e.stopPropagation()
                              onMarkGroupDone(group.id)
                            }}
                          >
                            {t('run:distributionGroups.markGroupDone')}
                          </button>
                        )}
                        {!group.is_default && run.state === 'distributing' && run.current_user_is_leader && (
                          <button
                            className="btn btn-sm btn-secondary"
                            onClick={(e) => {
                              e.stopPropagation()
                              onDeleteGroup(group.id)
                            }}
                            title={t('run:distributionGroups.deleteGroup')}
                          >
                            ✕
                          </button>
                        )}
                        <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
                      </div>
                    </div>
                    {isExpanded && (
                      <div className="distribution-group-content">
                        {sortedProducts.length > 0 && (
                          <div className="group-product-summary">
                            <div className="group-product-summary-title">{t('run:distributionGroups.productTotals')}</div>
                            {sortedProducts.map(p => {
                              const runProduct = run.products.find(rp => rp.id === p.productId)
                              const purchasedTotal = runProduct?.purchased_quantity ?? 0
                              return (
                                <div key={p.productId} className="group-product-summary-item">
                                  <span>{p.name}: {p.quantity}{p.unit ? ` ${p.unit}` : ''}{purchasedTotal > 0 && <span className="remaining-info"> / {purchasedTotal}</span>}</span>
                                  <span>{p.cost.toFixed(2)} RSD</span>
                                </div>
                              )
                            })}
                          </div>
                        )}
                        {group.users.length === 0 ? (
                          <div className="empty-state" style={{ padding: '0.5rem' }}>
                            <p style={{ fontSize: '0.9rem' }}>{t('run:empty.noUsersInGroup')}</p>
                          </div>
                        ) : (
                          group.users.map(user => (
                            <UserCard
                              key={user.user_id}
                              user={user}
                              run={run}
                              expandedUserId={expandedUserId}
                              onToggleExpand={onToggleExpand}
                              isLeaderOrHelper={isLeaderOrHelper}
                              onMarkPickedUp={onMarkPickedUp}
                              onMarkAllPickedUp={onMarkAllPickedUp}
                              markPickedUpPending={markPickedUpPending}
                              groups={distributionGroups}
                              onAssignUserToGroup={onAssignUserToGroup}
                            />
                          ))
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          ) : (
            /* Single group (default): render flat user cards as before */
            <div className="distribution-list">
              {singleGroupUsers.map(user => (
                <UserCard
                  key={user.user_id}
                  user={user}
                  run={run}
                  expandedUserId={expandedUserId}
                  onToggleExpand={onToggleExpand}
                  isLeaderOrHelper={isLeaderOrHelper}
                  onMarkPickedUp={onMarkPickedUp}
                  onMarkAllPickedUp={onMarkAllPickedUp}
                  markPickedUpPending={markPickedUpPending}
                />
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
