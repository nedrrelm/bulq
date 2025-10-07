import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useParams } from 'react-router-dom'
import './App.css'
import { API_BASE_URL } from './config'
import type { User } from './types/user'
import type { ProductSearchResult } from './types/product'
import Login from './components/Login'
import Groups from './components/Groups'
import GroupPage from './components/GroupPage'
import RunPage from './components/RunPage'
import JoinGroup from './components/JoinGroup'
import ShoppingPage from './components/ShoppingPage'
import DistributionPage from './components/DistributionPage'
import ProductPage from './components/ProductPage'
import ErrorBoundary from './components/ErrorBoundary'

interface BackendResponse {
  message: string
}

interface HealthResponse {
  status: string
}

// Wrapper components that use params and navigation
function GroupPageWrapper({ user, onLogout }: { user: User; onLogout: () => void }) {
  const { groupId } = useParams<{ groupId: string }>()
  const navigate = useNavigate()

  if (!groupId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout user={user} onLogout={onLogout}>
      <GroupPage
        groupId={groupId}
        onBack={() => navigate('/')}
        onRunSelect={(runId) => navigate(`/runs/${runId}`)}
      />
    </AppLayout>
  )
}

function RunPageWrapper({ user, onLogout }: { user: User; onLogout: () => void }) {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()

  if (!runId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout user={user} onLogout={onLogout}>
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

function ShoppingPageWrapper({ user, onLogout }: { user: User; onLogout: () => void }) {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()

  if (!runId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout user={user} onLogout={onLogout}>
      <ShoppingPage
        runId={runId}
        onBack={() => navigate(`/runs/${runId}`)}
      />
    </AppLayout>
  )
}

function DistributionPageWrapper({ user, onLogout }: { user: User; onLogout: () => void }) {
  const { runId } = useParams<{ runId: string }>()
  const navigate = useNavigate()

  if (!runId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout user={user} onLogout={onLogout}>
      <DistributionPage
        runId={runId}
        onBack={() => navigate(`/runs/${runId}`)}
      />
    </AppLayout>
  )
}

function ProductPageWrapper({ user, onLogout }: { user: User; onLogout: () => void }) {
  const { productId } = useParams<{ productId: string }>()
  const navigate = useNavigate()

  if (!productId) {
    navigate('/')
    return null
  }

  return (
    <AppLayout user={user} onLogout={onLogout}>
      <ProductPage
        productId={productId}
        onBack={() => navigate('/')}
      />
    </AppLayout>
  )
}

function JoinGroupWrapper({ user, onLogout }: { user: User; onLogout: () => void }) {
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

function DashboardWrapper({ user, onLogout }: { user: User; onLogout: () => void }) {
  const navigate = useNavigate()

  return (
    <AppLayout user={user} onLogout={onLogout}>
      <Groups
        onGroupSelect={(groupId) => navigate(`/groups/${groupId}`)}
        onRunSelect={(runId) => navigate(`/runs/${runId}`)}
        onProductSelect={(productId) => navigate(`/products/${productId}`)}
      />
    </AppLayout>
  )
}

// Shared layout component with header
function AppLayout({ user, onLogout, children }: { user: User; onLogout: () => void; children: React.ReactNode }) {
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<ProductSearchResult[]>([])
  const [searching, setSearching] = useState(false)

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
        <h1 onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>Bulq 📦</h1>

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
          <button onClick={onLogout} className="logout-button">
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

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [backendMessage, setBackendMessage] = useState<string>('')
  const [healthStatus, setHealthStatus] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  // Check if user is already logged in
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
          credentials: 'include'
        })
        if (response.ok) {
          const userData: User = await response.json()
          setUser(userData)
        }
      } catch (err) {
        // User not logged in, which is fine
      }
    }

    checkAuth()
  }, [])

  useEffect(() => {
    const fetchBackendData = async () => {
      try {
        setLoading(true)
        setError('')

        // Test hello world endpoint
        const helloResponse = await fetch(`${API_BASE_URL}/`)
        if (!helloResponse.ok) {
          throw new Error(`HTTP error! status: ${helloResponse.status}`)
        }
        const helloData: BackendResponse = await helloResponse.json()
        setBackendMessage(helloData.message)

        // Test health endpoint
        const healthResponse = await fetch(`${API_BASE_URL}/health`)
        if (!healthResponse.ok) {
          throw new Error(`HTTP error! status: ${healthResponse.status}`)
        }
        const healthData: HealthResponse = await healthResponse.json()
        setHealthStatus(healthData.status)

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to connect to backend')
      } finally {
        setLoading(false)
      }
    }

    fetchBackendData()
  }, [])

  const handleLogin = (userData: User) => {
    setUser(userData)
  }

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      })
      setUser(null)
      window.location.href = '/'
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  // Show login page if not authenticated
  if (!user) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardWrapper user={user} onLogout={handleLogout} />} />
        <Route path="/groups/:groupId" element={<GroupPageWrapper user={user} onLogout={handleLogout} />} />
        <Route path="/runs/:runId" element={<RunPageWrapper user={user} onLogout={handleLogout} />} />
        <Route path="/shopping/:runId" element={<ShoppingPageWrapper user={user} onLogout={handleLogout} />} />
        <Route path="/distribution/:runId" element={<DistributionPageWrapper user={user} onLogout={handleLogout} />} />
        <Route path="/products/:productId" element={<ProductPageWrapper user={user} onLogout={handleLogout} />} />
        <Route path="/invite/:inviteToken" element={<JoinGroupWrapper user={user} onLogout={handleLogout} />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
