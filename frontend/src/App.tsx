import { useState, useEffect, lazy, Suspense, useCallback } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useParams } from 'react-router-dom'
import './styles/App.css'
import './styles/dark-mode.css'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { NotificationProvider } from './contexts/NotificationContext'
import { searchApi } from './api'
import type { SearchResults } from './api'
import { debounce } from './utils/validation'
import Login from './components/Login'
import Groups from './components/Groups'
import ErrorBoundary from './components/ErrorBoundary'
import { NotificationBadge } from './components/NotificationBadge'
import { ProfileButton } from './components/ProfileButton'

// Lazy load route components for code splitting
const GroupPage = lazy(() => import('./components/GroupPage'))
const ManageGroupPage = lazy(() => import('./components/ManageGroupPage'))
const RunPage = lazy(() => import('./components/RunPage'))
const JoinGroup = lazy(() => import('./components/JoinGroup'))
const ShoppingPage = lazy(() => import('./components/ShoppingPage'))
const ProductPage = lazy(() => import('./components/ProductPage'))
const StorePage = lazy(() => import('./components/StorePage'))
const NotificationPage = lazy(() => import('./pages/NotificationPage'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))

// Wrapper components for lazy loading
function GroupPageWrapper() {
  return (
    <AppLayout>
      <GroupPage />
    </AppLayout>
  )
}

function RunPageWrapper() {
  return (
    <AppLayout>
      <RunPage />
    </AppLayout>
  )
}

function ShoppingPageWrapper() {
  return (
    <AppLayout>
      <ShoppingPage />
    </AppLayout>
  )
}

function ProductPageWrapper() {
  const { productId } = useParams<{ productId: string }>()
  const navigate = useNavigate()

  if (!productId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout>
      <ProductPage
        productId={productId}
        onBack={() => navigate('/')}
      />
    </AppLayout>
  )
}

function StorePageWrapper() {
  const { storeId } = useParams<{ storeId: string }>()
  const navigate = useNavigate()

  if (!storeId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout>
      <StorePage
        storeId={storeId}
        onBack={() => navigate('/')}
      />
    </AppLayout>
  )
}

function ManageGroupPageWrapper() {
  return (
    <AppLayout>
      <ManageGroupPage />
    </AppLayout>
  )
}

function JoinGroupWrapper() {
  const { inviteToken } = useParams<{ inviteToken: string }>()
  const navigate = useNavigate()

  if (!inviteToken) {
    navigate('/')
    return null
  }

  return (
    <JoinGroup
      inviteToken={inviteToken}
      onJoinSuccess={() => navigate('/')}
    />
  )
}

function DashboardWrapper() {
  const navigate = useNavigate()

  return (
    <AppLayout>
      <Groups
        onGroupSelect={(groupId) => navigate(`/groups/${groupId}`)}
        onRunSelect={(runId) => navigate(`/runs/${runId}`)}
      />
    </AppLayout>
  )
}

function NotificationPageWrapper() {
  return (
    <AppLayout>
      <NotificationPage />
    </AppLayout>
  )
}

function AdminPageWrapper() {
  return (
    <AppLayout>
      <AdminPage />
    </AppLayout>
  )
}

function ProfilePageWrapper() {
  return (
    <AppLayout>
      <ProfilePage />
    </AppLayout>
  )
}

// Shared layout component with header
function AppLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null)
  const [searching, setSearching] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  if (!user) return null

  const performSearch = async (query: string) => {
    if (query.trim().length < 2) {
      setSearchResults(null)
      return
    }

    try {
      setSearching(true)
      console.log('Searching for:', query)
      const results = await searchApi.searchAll(query)
      console.log('Search results:', results)
      console.log('Type of results:', typeof results)
      console.log('Products:', results.products, 'Type:', typeof results.products, 'Is array:', Array.isArray(results.products))
      console.log('Stores:', results.stores, 'Type:', typeof results.stores, 'Is array:', Array.isArray(results.stores))
      console.log('Groups:', results.groups, 'Type:', typeof results.groups, 'Is array:', Array.isArray(results.groups))
      setSearchResults(results)
    } catch (err) {
      console.error('=== SEARCH FAILED ===')
      console.error('Error:', err)
      console.error('Error type:', typeof err)
      console.error('Error message:', err instanceof Error ? err.message : String(err))
      console.error('Error stack:', err instanceof Error ? err.stack : 'N/A')
      console.error('=====================')
      setSearchResults(null)
    } finally {
      setSearching(false)
    }
  }

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedSearch = useCallback(debounce(performSearch, 300), [])

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    debouncedSearch(query)
  }

  // Apply dark mode on initial load
  useEffect(() => {
    if (user?.dark_mode) {
      document.body.classList.add('dark-mode')
    } else {
      document.body.classList.remove('dark-mode')
    }
  }, [user?.dark_mode])

  // Close search dropdown and menu on ESC key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSearchQuery('')
        setSearchResults(null)
        setMenuOpen(false)
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [])

  const hasResults = searchResults && (
    (searchResults.products?.length ?? 0) > 0 ||
    (searchResults.stores?.length ?? 0) > 0 ||
    (searchResults.groups?.length ?? 0) > 0
  )

  const closeSearch = () => {
    setSearchQuery('')
    setSearchResults(null)
  }

  const handleMenuItemClick = (action: () => void) => {
    action()
    setMenuOpen(false)
  }

  return (
    <div className="app">
      <header>
        <h1 onClick={() => navigate('/')} className="clickable">Bulq 📦</h1>

        <div className="header-search">
          <input
            type="text"
            placeholder="Search products, stores, groups..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="form-input"
          />
          {hasResults && (
            <div className="search-dropdown">
              {(searchResults?.products?.length ?? 0) > 0 && (
                <>
                  <div className="search-category-label">Products</div>
                  {searchResults!.products!.map((product: { id: string; name: string; brand: string | null; stores: { store_name: string; price: number | null }[] }) => (
                    <div
                      key={`product-${product.id}`}
                      className="search-result-item"
                      onClick={() => {
                        navigate(`/products/${product.id}`)
                        closeSearch()
                      }}
                    >
                      <div className="product-info">
                        <strong>{product.name}</strong>
                        {product.brand && <span className="product-brand">{product.brand}</span>}
                        {product.stores.length > 0 && (
                          <span className="product-store">
                            {product.stores.map((s: { store_name: string; price: number | null }) => s.store_name).join(', ')}
                          </span>
                        )}
                      </div>
                      {product.stores.length > 0 && product.stores[0] && product.stores[0].price && (
                        <span className="product-price">${product.stores[0].price.toFixed(2)}</span>
                      )}
                    </div>
                  ))}
                </>
              )}

              {(searchResults?.stores?.length ?? 0) > 0 && (
                <>
                  {(searchResults?.products?.length ?? 0) > 0 && <div className="search-divider" />}
                  <div className="search-category-label">Stores</div>
                  {searchResults!.stores!.map((store: { id: string; name: string; address: string | null }) => (
                    <div
                      key={`store-${store.id}`}
                      className="search-result-item"
                      onClick={() => {
                        navigate(`/stores/${store.id}`)
                        closeSearch()
                      }}
                    >
                      <div className="product-info">
                        <strong>{store.name}</strong>
                        {store.address && <span className="product-store">{store.address}</span>}
                      </div>
                    </div>
                  ))}
                </>
              )}

              {(searchResults?.groups?.length ?? 0) > 0 && (
                <>
                  {((searchResults?.products?.length ?? 0) > 0 || (searchResults?.stores?.length ?? 0) > 0) && (
                    <div className="search-divider" />
                  )}
                  <div className="search-category-label">Groups</div>
                  {searchResults!.groups!.map((group: { id: string; name: string; member_count: number }) => (
                    <div
                      key={`group-${group.id}`}
                      className="search-result-item"
                      onClick={() => {
                        navigate(`/groups/${group.id}`)
                        closeSearch()
                      }}
                    >
                      <div className="product-info">
                        <strong>{group.name}</strong>
                        <span className="product-store">{group.member_count} members</span>
                      </div>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
          {searchQuery.trim().length >= 2 && !searching && !hasResults && (
            <div className="search-dropdown">
              <div className="search-no-results">No results found</div>
            </div>
          )}
        </div>

        <div className="user-info">
          <NotificationBadge />
          <ProfileButton />

          {/* Hamburger button - mobile only */}
          <button
            className={`hamburger-button ${menuOpen ? 'open' : ''}`}
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Menu"
          >
            <div className="hamburger-icon">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </button>

          {/* Desktop buttons - desktop only */}
          <div className="desktop-buttons">
            {user.is_admin && (
              <button onClick={() => navigate('/admin')} className="admin-button">
                Admin
              </button>
            )}
            <button onClick={logout} className="logout-button">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Mobile drawer menu */}
      {menuOpen && (
        <>
          <div className="menu-overlay" onClick={() => setMenuOpen(false)} />
          <div className="mobile-drawer">
            <div className="drawer-search">
              <input
                type="text"
                placeholder="Search products, stores, groups..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="form-input"
              />
              {hasResults && (
                <div className="search-dropdown">
                  {(searchResults?.products?.length ?? 0) > 0 && (
                    <>
                      <div className="search-category-label">Products</div>
                      {searchResults!.products!.map((product: { id: string; name: string; brand: string | null; stores: { store_name: string; price: number | null }[] }) => (
                        <div
                          key={`product-${product.id}`}
                          className="search-result-item"
                          onClick={() => {
                            navigate(`/products/${product.id}`)
                            closeSearch()
                            setMenuOpen(false)
                          }}
                        >
                          <div className="product-info">
                            <strong>{product.name}</strong>
                            {product.brand && <span className="product-brand">{product.brand}</span>}
                            {product.stores.length > 0 && (
                              <span className="product-store">
                                {product.stores.map((s: { store_name: string; price: number | null }) => s.store_name).join(', ')}
                              </span>
                            )}
                          </div>
                          {product.stores.length > 0 && product.stores[0] && product.stores[0].price && (
                            <span className="product-price">${product.stores[0].price.toFixed(2)}</span>
                          )}
                        </div>
                      ))}
                    </>
                  )}

                  {(searchResults?.stores?.length ?? 0) > 0 && (
                    <>
                      {(searchResults?.products?.length ?? 0) > 0 && <div className="search-divider" />}
                      <div className="search-category-label">Stores</div>
                      {searchResults!.stores!.map((store: { id: string; name: string; address: string | null }) => (
                        <div
                          key={`store-${store.id}`}
                          className="search-result-item"
                          onClick={() => {
                            navigate(`/stores/${store.id}`)
                            closeSearch()
                            setMenuOpen(false)
                          }}
                        >
                          <div className="product-info">
                            <strong>{store.name}</strong>
                            {store.address && <span className="product-store">{store.address}</span>}
                          </div>
                        </div>
                      ))}
                    </>
                  )}

                  {(searchResults?.groups?.length ?? 0) > 0 && (
                    <>
                      {((searchResults?.products?.length ?? 0) > 0 || (searchResults?.stores?.length ?? 0) > 0) && (
                        <div className="search-divider" />
                      )}
                      <div className="search-category-label">Groups</div>
                      {searchResults!.groups!.map((group: { id: string; name: string; member_count: number }) => (
                        <div
                          key={`group-${group.id}`}
                          className="search-result-item"
                          onClick={() => {
                            navigate(`/groups/${group.id}`)
                            closeSearch()
                            setMenuOpen(false)
                          }}
                        >
                          <div className="product-info">
                            <strong>{group.name}</strong>
                            <span className="product-store">{group.member_count} members</span>
                          </div>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              )}
              {searchQuery.trim().length >= 2 && !searching && !hasResults && (
                <div className="search-dropdown">
                  <div className="search-no-results">No results found</div>
                </div>
              )}
            </div>
            <div className="drawer-divider" />
            <button
              onClick={() => handleMenuItemClick(() => navigate('/profile'))}
              className="drawer-item"
            >
              Profile
            </button>
            {user.is_admin && (
              <button
                onClick={() => handleMenuItemClick(() => navigate('/admin'))}
                className="drawer-item"
              >
                Admin Panel
              </button>
            )}
            <button
              onClick={() => handleMenuItemClick(logout)}
              className="drawer-item"
            >
              Logout
            </button>
          </div>
        </>
      )}

      <main className={window.location.pathname === '/' ? 'dashboard' : ''}>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </main>
    </div>
  )
}

function AppRoutes() {
  const { user, login, loading } = useAuth()
  const navigate = useNavigate()

  // Show loading state while checking auth
  if (loading) {
    return (
      <div className="app">
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          fontSize: '1.2rem',
          color: 'var(--color-text)'
        }}>
          Loading...
        </div>
      </div>
    )
  }

  // Show login page if not authenticated
  if (!user) {
    return <Login onLogin={(userData) => {
      login(userData)
      navigate('/')
    }} />
  }

  return (
    <Suspense fallback={
      <div className="app">
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          fontSize: '1.2rem',
          color: 'var(--color-text)'
        }}>
          Loading...
        </div>
      </div>
    }>
      <Routes>
        <Route path="/" element={<DashboardWrapper />} />
        <Route path="/groups/:groupId" element={<GroupPageWrapper />} />
        <Route path="/groups/:groupId/manage" element={<ManageGroupPageWrapper />} />
        <Route path="/runs/:runId" element={<RunPageWrapper />} />
        <Route path="/shopping/:runId" element={<ShoppingPageWrapper />} />
        <Route path="/products/:productId" element={<ProductPageWrapper />} />
        <Route path="/stores/:storeId" element={<StorePageWrapper />} />
        <Route path="/notifications" element={<NotificationPageWrapper />} />
        <Route path="/profile" element={<ProfilePageWrapper />} />
        <Route path="/admin" element={<AdminPageWrapper />} />
        <Route path="/invite/:inviteToken" element={<JoinGroupWrapper />} />
      </Routes>
    </Suspense>
  )
}

function App() {
  const basePath = import.meta.env.VITE_BASE_PATH || '/'
  const basename = basePath === '/' ? undefined : basePath

  return (
    <AuthProvider>
      <NotificationProvider>
        <BrowserRouter basename={basename}>
          <AppRoutes />
        </BrowserRouter>
      </NotificationProvider>
    </AuthProvider>
  )
}

export default App
