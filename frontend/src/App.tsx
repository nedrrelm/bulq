import { useState, useEffect, lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useParams } from 'react-router-dom'
import './App.css'
import { API_BASE_URL } from './config'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import type { ProductSearchResult } from './types/product'
import Login from './components/Login'
import Groups from './components/Groups'
import ErrorBoundary from './components/ErrorBoundary'

// Lazy load route components for code splitting
const GroupPage = lazy(() => import('./components/GroupPage'))
const RunPage = lazy(() => import('./components/RunPage'))
const JoinGroup = lazy(() => import('./components/JoinGroup'))
const ShoppingPage = lazy(() => import('./components/ShoppingPage'))
const DistributionPage = lazy(() => import('./components/DistributionPage'))
const ProductPage = lazy(() => import('./components/ProductPage'))

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
  const [searchResults, setSearchResults] = useState<ProductSearchResult[]>([])
  const [searching, setSearching] = useState(false)

  if (!user) return null

  const handleSearch = async (query: string) => {
    setSearchQuery(query)

    if (query.trim().length < 2) {
      setSearchResults([])
      return
    }

    try {
      setSearching(true)
      const response = await fetch(`${API_BASE_URL}/products/search?q=${encodeURIComponent(query)}`, {
        credentials: 'include'
      })

      if (response.ok) {
        const results: ProductSearchResult[] = await response.json()
        setSearchResults(results)
      } else {
        setSearchResults([])
      }
    } catch (err) {
      console.error('Search failed:', err)
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  // Close search dropdown on ESC key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setSearchQuery('')
        setSearchResults([])
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [])

  return (
    <div className="app">
      <header>
        <h1 onClick={() => navigate('/')} className="clickable">Bulq 📦</h1>

        <div className="header-search">
          <input
            type="text"
            placeholder="Search products..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="form-input"
          />
          {searchResults.length > 0 && (
            <div className="search-dropdown">
              {searchResults.map((product) => (
                <div
                  key={product.id}
                  className="search-result-item"
                  onClick={() => {
                    navigate(`/products/${product.id}`)
                    setSearchQuery('')
                    setSearchResults([])
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
            </div>
          )}
          {searchQuery.trim().length >= 2 && !searching && searchResults.length === 0 && (
            <div className="search-dropdown">
              <div className="search-no-results">No products found</div>
            </div>
          )}
        </div>

        <div className="user-info">
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
          <Route path="/runs/:runId" element={<RunPageWrapper />} />
          <Route path="/shopping/:runId" element={<ShoppingPageWrapper />} />
          <Route path="/distribution/:runId" element={<DistributionPageWrapper />} />
          <Route path="/products/:productId" element={<ProductPageWrapper />} />
          <Route path="/invite/:inviteToken" element={<JoinGroupWrapper />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

export default App
