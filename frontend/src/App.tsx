import { useState, useEffect, lazy, Suspense, useCallback } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useParams } from 'react-router-dom'
import './App.css'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { NotificationProvider } from './contexts/NotificationContext'
import { searchApi } from './api'
import type { SearchResults } from './api'
import { debounce } from './utils/validation'
import Login from './components/Login'
import Groups from './components/Groups'
import ErrorBoundary from './components/ErrorBoundary'
import { NotificationBadge } from './components/NotificationBadge'

// Lazy load route components for code splitting
const GroupPage = lazy(() => import('./components/GroupPage'))
const ManageGroupPage = lazy(() => import('./components/ManageGroupPage'))
const RunPage = lazy(() => import('./components/RunPage'))
const JoinGroup = lazy(() => import('./components/JoinGroup'))
const ShoppingPage = lazy(() => import('./components/ShoppingPage'))
const DistributionPage = lazy(() => import('./components/DistributionPage'))
const ProductPage = lazy(() => import('./components/ProductPage'))
const StorePage = lazy(() => import('./components/StorePage'))
const NotificationPage = lazy(() => import('./pages/NotificationPage'))

// Wrapper components that use params and navigation
function GroupPageWrapper() {
  const { groupId } = useParams<{ groupId: string }>()
  const navigate = useNavigate()

  if (!groupId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout>
      <GroupPage
        groupId={groupId}
        onBack={() => navigate('/')}
        onRunSelect={(runId) => navigate(`/runs/${runId}`)}
        onManageSelect={(groupId) => navigate(`/groups/${groupId}/manage`)}
      />
    </AppLayout>
  )
}

function RunPageWrapper() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()
  const { user } = useAuth()

  if (!runId || !user) {
    navigate('/')
    return null
  }

  return (
    <AppLayout>
      <RunPage
        runId={runId}
        userId={user.id}
        onBack={(groupId) => groupId ? navigate(`/groups/${groupId}`) : navigate('/')}
        onShoppingSelect={(id) => navigate(`/shopping/${id}`)}
        onDistributionSelect={(id) => navigate(`/distribution/${id}`)}
      />
    </AppLayout>
  )
}

function ShoppingPageWrapper() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()

  if (!runId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout>
      <ShoppingPage
        runId={runId}
        onBack={() => navigate(`/runs/${runId}`)}
      />
    </AppLayout>
  )
}

function DistributionPageWrapper() {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()

  if (!runId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout>
      <DistributionPage
        runId={runId}
        onBack={() => navigate(`/runs/${runId}`)}
      />
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
  const { groupId } = useParams<{ groupId: string }>()
  const navigate = useNavigate()

  if (!groupId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout>
      <ManageGroupPage
        groupId={groupId}
        onBack={() => navigate(`/groups/${groupId}`)}
      />
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

// Shared layout component with header
function AppLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null)
  const [searching, setSearching] = useState(false)

  if (!user) return null

  const performSearch = async (query: string) => {
    if (query.trim().length < 2) {
      setSearchResults(null)
      return
    }

    try {
      setSearching(true)
      const results = await searchApi.searchAll(query)
      setSearchResults(results)
    } catch (err) {
      console.error('Search failed:', err)
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

  // Close search dropdown on ESC key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSearchQuery('')
        setSearchResults(null)
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [])

  const hasResults = searchResults && (
    searchResults.products.length > 0 ||
    searchResults.stores.length > 0 ||
    searchResults.groups.length > 0
  )

  const closeSearch = () => {
    setSearchQuery('')
    setSearchResults(null)
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
              {searchResults!.products.length > 0 && (
                <>
                  <div className="search-category-label">Products</div>
                  {searchResults!.products.map((product) => (
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
                        <span className="product-store">{product.store_name}</span>
                      </div>
                      {product.base_price && (
                        <span className="product-price">${product.base_price.toFixed(2)}</span>
                      )}
                    </div>
                  ))}
                </>
              )}

              {searchResults!.stores.length > 0 && (
                <>
                  {searchResults!.products.length > 0 && <div className="search-divider" />}
                  <div className="search-category-label">Stores</div>
                  {searchResults!.stores.map((store) => (
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

              {searchResults!.groups.length > 0 && (
                <>
                  {(searchResults!.products.length > 0 || searchResults!.stores.length > 0) && (
                    <div className="search-divider" />
                  )}
                  <div className="search-category-label">Groups</div>
                  {searchResults!.groups.map((group) => (
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
          <span>Welcome, {user.name}!</span>
          <button onClick={logout} className="logout-button">
            Logout
          </button>
        </div>
      </header>

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
    return <Login onLogin={login} />
  }

  return (
    <BrowserRouter>
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
          <Route path="/distribution/:runId" element={<DistributionPageWrapper />} />
          <Route path="/products/:productId" element={<ProductPageWrapper />} />
          <Route path="/stores/:storeId" element={<StorePageWrapper />} />
          <Route path="/notifications" element={<NotificationPage />} />
          <Route path="/invite/:inviteToken" element={<JoinGroupWrapper />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <AppRoutes />
      </NotificationProvider>
    </AuthProvider>
  )
}

export default App
