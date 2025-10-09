import { useState, useEffect } from 'react'
import { adminApi } from '../api/admin'
import type { AdminUser, AdminProduct, AdminStore } from '../api/admin'
import '../styles/pages/AdminPage.css'

type TabType = 'users' | 'products' | 'stores'

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<TabType>('users')
  const [search, setSearch] = useState('')
  const [verifiedFilter, setVerifiedFilter] = useState<boolean | undefined>(undefined)

  // Users
  const [users, setUsers] = useState<AdminUser[]>([])
  const [loadingUsers, setLoadingUsers] = useState(false)

  // Products
  const [products, setProducts] = useState<AdminProduct[]>([])
  const [loadingProducts, setLoadingProducts] = useState(false)

  // Stores
  const [stores, setStores] = useState<AdminStore[]>([])
  const [loadingStores, setLoadingStores] = useState(false)

  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers()
    } else if (activeTab === 'products') {
      fetchProducts()
    } else if (activeTab === 'stores') {
      fetchStores()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, search, verifiedFilter])

  const fetchUsers = async () => {
    setLoadingUsers(true)
    try {
      console.log('Fetching users with:', { search, verifiedFilter })
      const data = await adminApi.getUsers(search || undefined, verifiedFilter)
      console.log('Fetched users:', data)
      setUsers(data)
    } catch (err) {
      console.error('Failed to fetch users:', err)
    } finally {
      setLoadingUsers(false)
    }
  }

  const fetchProducts = async () => {
    setLoadingProducts(true)
    try {
      const data = await adminApi.getProducts(search || undefined, verifiedFilter)
      setProducts(data)
    } catch (err) {
      console.error('Failed to fetch products:', err)
    } finally {
      setLoadingProducts(false)
    }
  }

  const fetchStores = async () => {
    setLoadingStores(true)
    try {
      const data = await adminApi.getStores(search || undefined, verifiedFilter)
      setStores(data)
    } catch (err) {
      console.error('Failed to fetch stores:', err)
    } finally {
      setLoadingStores(false)
    }
  }

  const toggleUserVerification = async (userId: string) => {
    try {
      await adminApi.toggleUserVerification(userId)
      fetchUsers()
    } catch (err) {
      console.error('Failed to toggle user verification:', err)
    }
  }

  const toggleProductVerification = async (productId: string) => {
    try {
      await adminApi.toggleProductVerification(productId)
      fetchProducts()
    } catch (err) {
      console.error('Failed to toggle product verification:', err)
    }
  }

  const toggleStoreVerification = async (storeId: string) => {
    try {
      await adminApi.toggleStoreVerification(storeId)
      fetchStores()
    } catch (err) {
      console.error('Failed to toggle store verification:', err)
    }
  }

  return (
    <div className="admin-page">
      <h1>Admin Console</h1>

      <div className="admin-tabs">
        <button
          className={activeTab === 'users' ? 'active' : ''}
          onClick={() => setActiveTab('users')}
        >
          Users
        </button>
        <button
          className={activeTab === 'products' ? 'active' : ''}
          onClick={() => setActiveTab('products')}
        >
          Products
        </button>
        <button
          className={activeTab === 'stores' ? 'active' : ''}
          onClick={() => setActiveTab('stores')}
        >
          Stores
        </button>
      </div>

      <div className="admin-filters">
        <input
          type="text"
          placeholder="Search by name, email, or ID..."
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
          <option value="all">All</option>
          <option value="true">Verified</option>
          <option value="false">Unverified</option>
        </select>
      </div>

      {activeTab === 'users' && (
        <div className="admin-content">
          {loadingUsers ? (
            <p>Loading...</p>
          ) : (
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>ID</th>
                  <th>Admin</th>
                  <th>Verified</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users?.map((user) => (
                  <tr key={user.id}>
                    <td>{user.name}</td>
                    <td>{user.email}</td>
                    <td className="id-cell">{user.id}</td>
                    <td>{user.is_admin ? '✓' : ''}</td>
                    <td>{user.verified ? '✓' : '✗'}</td>
                    <td>
                      <button
                        onClick={() => toggleUserVerification(user.id)}
                        className="btn-small"
                      >
                        {user.verified ? 'Unverify' : 'Verify'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'products' && (
        <div className="admin-content">
          {loadingProducts ? (
            <p>Loading...</p>
          ) : (
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Brand</th>
                  <th>Store</th>
                  <th>ID</th>
                  <th>Verified</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {products?.map((product) => (
                  <tr key={product.id}>
                    <td>{product.name}</td>
                    <td>{product.brand || '-'}</td>
                    <td>{product.store_name || '-'}</td>
                    <td className="id-cell">{product.id}</td>
                    <td>{product.verified ? '✓' : '✗'}</td>
                    <td>
                      <button
                        onClick={() => toggleProductVerification(product.id)}
                        className="btn-small"
                      >
                        {product.verified ? 'Unverify' : 'Verify'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'stores' && (
        <div className="admin-content">
          {loadingStores ? (
            <p>Loading...</p>
          ) : (
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Address</th>
                  <th>Chain</th>
                  <th>ID</th>
                  <th>Verified</th>
                  <th>Actions</th>
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
                        onClick={() => toggleStoreVerification(store.id)}
                        className="btn-small"
                      >
                        {store.verified ? 'Unverify' : 'Verify'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
