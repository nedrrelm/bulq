import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { adminApi } from '../api/admin'
import type { AdminUser, AdminProduct, AdminStore, AdminGroup } from '../api/admin'
import EditProductPopup from '../components/EditProductPopup'
import EditStorePopup from '../components/EditStorePopup'
import EditUserPopup from '../components/EditUserPopup'
import { logger } from '../utils/logger'
import '../styles/pages/AdminPage.css'

type TabType = 'users' | 'products' | 'stores' | 'groups'

const LIMIT = 100

export default function AdminPage() {
  const { t } = useTranslation(['admin', 'common'])
  const [activeTab, setActiveTab] = useState<TabType>('users')
  const [search, setSearch] = useState('')
  const [verifiedFilter, setVerifiedFilter] = useState<boolean | undefined>(undefined)

  // Pagination state
  const [usersOffset, setUsersOffset] = useState(0)
  const [productsOffset, setProductsOffset] = useState(0)
  const [storesOffset, setStoresOffset] = useState(0)
  const [groupsOffset, setGroupsOffset] = useState(0)

  // Users
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loadingUsers, setLoadingUsers] = useState(false)

  // Products
  const [products, setProducts] = useState<AdminProduct[]>([])
  const [loadingProducts, setLoadingProducts] = useState(false)

  // Stores
  const [stores, setStores] = useState<AdminStore[]>([])
  const [loadingStores, setLoadingStores] = useState(false)

  // Groups
  const [groups, setGroups] = useState<AdminGroup[]>([])
  const [loadingGroups, setLoadingGroups] = useState(false)

  // Edit popups
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null)
  const [editingProduct, setEditingProduct] = useState<AdminProduct | null>(null)
  const [editingStore, setEditingStore] = useState<AdminStore | null>(null)

  // Registration setting
  const [allowRegistration, setAllowRegistration] = useState(true)
  const [loadingRegistrationSetting, setLoadingRegistrationSetting] = useState(true)

  useEffect(() => {
    fetchRegistrationSetting()
  }, [])

  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers()
    } else if (activeTab === 'products') {
      fetchProducts()
    } else if (activeTab === 'stores') {
      fetchStores()
    } else if (activeTab === 'groups') {
      fetchGroups()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, search, verifiedFilter, usersOffset, productsOffset, storesOffset, groupsOffset])

  // Reset offsets when search or filter changes
  useEffect(() => {
    setUsersOffset(0)
    setProductsOffset(0)
    setStoresOffset(0)
    setGroupsOffset(0)
  }, [search, verifiedFilter])

  const fetchUsers = async () => {
    setLoadingUsers(true)
    try {
      const data = await adminApi.getUsers(search || undefined, verifiedFilter, LIMIT, usersOffset)
      setUsers(data)
    } catch (err) {
      logger.error('Failed to fetch users:', err)
    } finally {
      setLoadingUsers(false)
    }
  }

  const fetchProducts = async () => {
    setLoadingProducts(true)
    try {
      const data = await adminApi.getProducts(search || undefined, verifiedFilter, LIMIT, productsOffset)
      setProducts(data)
    } catch (err) {
      logger.error('Failed to fetch products:', err)
    } finally {
      setLoadingProducts(false)
    }
  }

  const fetchStores = async () => {
    setLoadingStores(true)
    try {
      const data = await adminApi.getStores(search || undefined, verifiedFilter, LIMIT, storesOffset)
      setStores(data)
    } catch (err) {
      logger.error('Failed to fetch stores:', err)
    } finally {
      setLoadingStores(false)
    }
  }

  const fetchGroups = async () => {
    setLoadingGroups(true)
    try {
      const data = await adminApi.getGroups(search || undefined, LIMIT, groupsOffset)
      setGroups(data)
    } catch (err) {
      logger.error('Failed to fetch groups:', err)
    } finally {
      setLoadingGroups(false)
    }
  }

  const toggleUserVerification = async (userId: string) => {
    try {
      // Optimistically update the UI
      setUsers(users.map(user =>
        user.id === userId ? { ...user, verified: !user.verified } : user
      ))
      await adminApi.toggleUserVerification(userId)
    } catch (err) {
      logger.error('Failed to toggle user verification:', err)
      // Revert on error
      fetchUsers()
    }
  }

  const toggleProductVerification = async (productId: string) => {
    try {
      // Optimistically update the UI
      setProducts(products.map(product =>
        product.id === productId ? { ...product, verified: !product.verified } : product
      ))
      await adminApi.toggleProductVerification(productId)
    } catch (err) {
      logger.error('Failed to toggle product verification:', err)
      // Revert on error
      fetchProducts()
    }
  }

  const toggleStoreVerification = async (storeId: string) => {
    try {
      // Optimistically update the UI
      setStores(stores.map(store =>
        store.id === storeId ? { ...store, verified: !store.verified } : store
      ))
      await adminApi.toggleStoreVerification(storeId)
    } catch (err) {
      logger.error('Failed to toggle store verification:', err)
      // Revert on error
      fetchStores()
    }
  }

  const fetchRegistrationSetting = async () => {
    setLoadingRegistrationSetting(true)
    try {
      const data = await adminApi.getRegistrationSetting()
      setAllowRegistration(data.allow_registration)
    } catch (err) {
      logger.error('Failed to fetch registration setting:', err)
    } finally {
      setLoadingRegistrationSetting(false)
    }
  }

  const toggleRegistration = async () => {
    try {
      const newValue = !allowRegistration
      setAllowRegistration(newValue)
      await adminApi.setRegistrationSetting(newValue)
    } catch (err) {
      logger.error('Failed to toggle registration:', err)
      // Revert on error
      setAllowRegistration(!allowRegistration)
    }
  }

  return (
    <div className="admin-page">
      <h1>{t('admin:title')}</h1>

      {/* Global Settings */}
      <div className="admin-settings">
        <div className="setting-row">
          <div>
            <h3>{t('admin:settings.allowRegistration')}</h3>
            <p>{t('admin:settings.allowRegistrationDescription')}</p>
          </div>
          <label className="toggle-switch">
            <input
              type="checkbox"
              checked={allowRegistration}
              onChange={toggleRegistration}
              disabled={loadingRegistrationSetting}
            />
            <span className="toggle-slider"></span>
          </label>
        </div>
      </div>

      <div className="admin-tabs">
        <button
          className={activeTab === 'users' ? 'active' : ''}
          onClick={() => setActiveTab('users')}
        >
          {t('admin:tabs.users')}
        </button>
        <button
          className={activeTab === 'products' ? 'active' : ''}
          onClick={() => setActiveTab('products')}
        >
          {t('admin:tabs.products')}
        </button>
        <button
          className={activeTab === 'stores' ? 'active' : ''}
          onClick={() => setActiveTab('stores')}
        >
          {t('admin:tabs.stores')}
        </button>
        <button
          className={activeTab === 'groups' ? 'active' : ''}
          onClick={() => setActiveTab('groups')}
        >
          {t('admin:tabs.groups')}
        </button>
      </div>

      <div className="admin-filters">
        <input
          type="text"
          placeholder={t('admin:search.placeholder')}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="form-input"
        />
        <select
          value={verifiedFilter === undefined ? 'all' : verifiedFilter.toString()}
          onChange={(e) => {
            const value = e.target.value
            setVerifiedFilter(value === 'all' ? undefined : value === 'true')
          }}
          className="form-input"
        >
          <option value="all">{t('admin:filters.all')}</option>
          <option value="true">{t('admin:filters.verified')}</option>
          <option value="false">{t('admin:filters.unverified')}</option>
        </select>
      </div>

      {activeTab === 'users' && (
        <div className="admin-content">
          {loadingUsers ? (
            <p>{t('common:loading')}</p>
          ) : (
            <>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>{t('admin:users.name')}</th>
                    <th>{t('admin:users.username')}</th>
                    <th>{t('admin:users.id')}</th>
                    <th>{t('admin:users.admin')}</th>
                    <th>{t('admin:users.verified')}</th>
                    <th>{t('admin:users.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {users?.map((user) => (
                    <tr key={user.id}>
                      <td>{user.name}</td>
                      <td>@{user.username}</td>
                      <td className="id-cell">{user.id}</td>
                      <td>{user.is_admin ? '✓' : ''}</td>
                      <td>{user.verified ? '✓' : '✗'}</td>
                      <td>
                        <button
                          onClick={() => setEditingUser(user)}
                          className="btn-small"
                          style={{ marginRight: '0.5rem' }}
                        >
                          {t('common:edit')}
                        </button>
                        <button
                          onClick={() => toggleUserVerification(user.id)}
                          className="btn-small"
                        >
                          {user.verified ? t('admin:actions.unverify') : t('admin:actions.verify')}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(usersOffset > 0 || users.length === LIMIT) && (
                <div className="pagination-controls">
                  <button
                    onClick={() => setUsersOffset(Math.max(0, usersOffset - LIMIT))}
                    disabled={usersOffset === 0}
                    className="btn btn-secondary"
                  >
                    {t('common:previous')}
                  </button>
                  <span className="pagination-info">
                    {t('common:showing')} {usersOffset + 1}-{usersOffset + users.length}
                  </span>
                  <button
                    onClick={() => setUsersOffset(usersOffset + LIMIT)}
                    disabled={users.length < LIMIT}
                    className="btn btn-secondary"
                  >
                    {t('common:next')}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'products' && (
        <div className="admin-content">
          {loadingProducts ? (
            <p>{t('common:loading')}</p>
          ) : (
            <>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>{t('admin:products.name')}</th>
                    <th>{t('admin:products.brand')}</th>
                    <th>{t('admin:products.unit')}</th>
                    <th>{t('admin:products.id')}</th>
                    <th>{t('admin:products.verified')}</th>
                    <th>{t('admin:products.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {products?.map((product) => (
                    <tr key={product.id}>
                      <td>{product.name}</td>
                      <td>{product.brand || '-'}</td>
                      <td>{product.unit || '-'}</td>
                      <td className="id-cell">{product.id}</td>
                      <td>{product.verified ? '✓' : '✗'}</td>
                      <td>
                        <button
                          onClick={() => setEditingProduct(product)}
                          className="btn-small"
                          style={{ marginRight: '0.5rem' }}
                        >
                          {t('common:edit')}
                        </button>
                        <button
                          onClick={() => toggleProductVerification(product.id)}
                          className="btn-small"
                        >
                          {product.verified ? t('admin:actions.unverify') : t('admin:actions.verify')}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(productsOffset > 0 || products.length === LIMIT) && (
                <div className="pagination-controls">
                  <button
                    onClick={() => setProductsOffset(Math.max(0, productsOffset - LIMIT))}
                    disabled={productsOffset === 0}
                    className="btn btn-secondary"
                  >
                    {t('common:previous')}
                  </button>
                  <span className="pagination-info">
                    {t('common:showing')} {productsOffset + 1}-{productsOffset + products.length}
                  </span>
                  <button
                    onClick={() => setProductsOffset(productsOffset + LIMIT)}
                    disabled={products.length < LIMIT}
                    className="btn btn-secondary"
                  >
                    {t('common:next')}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'stores' && (
        <div className="admin-content">
          {loadingStores ? (
            <p>{t('common:loading')}</p>
          ) : (
            <>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>{t('admin:stores.name')}</th>
                    <th>{t('admin:stores.address')}</th>
                    <th>{t('admin:stores.chain')}</th>
                    <th>{t('admin:stores.id')}</th>
                    <th>{t('admin:stores.verified')}</th>
                    <th>{t('admin:stores.actions')}</th>
                  </tr>
                </thead>
                <tbody>
                  {stores?.map((store) => (
                    <tr key={store.id}>
                      <td>{store.name}</td>
                      <td>{store.address || '-'}</td>
                      <td>{store.chain || '-'}</td>
                      <td className="id-cell">{store.id}</td>
                      <td>{store.verified ? '✓' : '✗'}</td>
                      <td>
                        <button
                          onClick={() => setEditingStore(store)}
                          className="btn-small"
                          style={{ marginRight: '0.5rem' }}
                        >
                          {t('common:edit')}
                        </button>
                        <button
                          onClick={() => toggleStoreVerification(store.id)}
                          className="btn-small"
                        >
                          {store.verified ? t('admin:actions.unverify') : t('admin:actions.verify')}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(storesOffset > 0 || stores.length === LIMIT) && (
                <div className="pagination-controls">
                  <button
                    onClick={() => setStoresOffset(Math.max(0, storesOffset - LIMIT))}
                    disabled={storesOffset === 0}
                    className="btn btn-secondary"
                  >
                    {t('common:previous')}
                  </button>
                  <span className="pagination-info">
                    {t('common:showing')} {storesOffset + 1}-{storesOffset + stores.length}
                  </span>
                  <button
                    onClick={() => setStoresOffset(storesOffset + LIMIT)}
                    disabled={stores.length < LIMIT}
                    className="btn btn-secondary"
                  >
                    {t('common:next')}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'groups' && (
        <div className="admin-content">
          {loadingGroups ? (
            <p>{t('common:loading')}</p>
          ) : (
            <>
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>{t('admin:groups.name')}</th>
                    <th>{t('admin:groups.creator')}</th>
                    <th>{t('admin:groups.memberCount')}</th>
                    <th>{t('admin:groups.id')}</th>
                    <th>{t('admin:groups.createdAt')}</th>
                  </tr>
                </thead>
                <tbody>
                  {groups?.map((group) => (
                    <tr key={group.id}>
                      <td>{group.name}</td>
                      <td>{group.creator_name}</td>
                      <td>{group.member_count}</td>
                      <td className="id-cell">{group.id}</td>
                      <td>{group.created_at ? new Date(group.created_at).toLocaleDateString() : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(groupsOffset > 0 || groups.length === LIMIT) && (
                <div className="pagination-controls">
                  <button
                    onClick={() => setGroupsOffset(Math.max(0, groupsOffset - LIMIT))}
                    disabled={groupsOffset === 0}
                    className="btn btn-secondary"
                  >
                    {t('common:previous')}
                  </button>
                  <span className="pagination-info">
                    {t('common:showing')} {groupsOffset + 1}-{groupsOffset + groups.length}
                  </span>
                  <button
                    onClick={() => setGroupsOffset(groupsOffset + LIMIT)}
                    disabled={groups.length < LIMIT}
                    className="btn btn-secondary"
                  >
                    {t('common:next')}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Edit Popups */}
      {editingUser && (
        <EditUserPopup
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSuccess={() => {
            setEditingUser(null)
            fetchUsers()
          }}
        />
      )}

      {editingProduct && (
        <EditProductPopup
          product={editingProduct}
          onClose={() => setEditingProduct(null)}
          onSuccess={() => {
            setEditingProduct(null)
            fetchProducts()
          }}
        />
      )}

      {editingStore && (
        <EditStorePopup
          store={editingStore}
          onClose={() => setEditingStore(null)}
          onSuccess={() => {
            setEditingStore(null)
            fetchStores()
          }}
        />
      )}
    </div>
  )
}
