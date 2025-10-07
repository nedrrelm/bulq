import { useState, useEffect } from 'react'
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

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [backendMessage, setBackendMessage] = useState<string>('')
  const [healthStatus, setHealthStatus] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [currentView, setCurrentView] = useState<'dashboard' | 'group' | 'run' | 'shopping' | 'distribution' | 'join' | 'product'>('dashboard')
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null)
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null)
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null)
  const [inviteToken, setInviteToken] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<ProductSearchResult[]>([])
  const [searching, setSearching] = useState(false)

  // Parse URL and set initial view based on pathname
  useEffect(() => {
    const path = window.location.pathname

    // Check for invite link
    const inviteMatch = path.match(/^\/invite\/(.+)$/)
    if (inviteMatch) {
      setInviteToken(inviteMatch[1])
      setCurrentView('join')
      return
    }

    // Check for product page
    const productMatch = path.match(/^\/products\/(.+)$/)
    if (productMatch) {
      setSelectedProductId(productMatch[1])
      setCurrentView('product')
      return
    }

    // Check for distribution page
    const distributionMatch = path.match(/^\/distribution\/(.+)$/)
    if (distributionMatch) {
      setSelectedRunId(distributionMatch[1])
      setCurrentView('distribution')
      return
    }

    // Check for shopping page
    const shoppingMatch = path.match(/^\/shopping\/(.+)$/)
    if (shoppingMatch) {
      setSelectedRunId(shoppingMatch[1])
      setCurrentView('shopping')
      return
    }

    // Check for run page
    const runMatch = path.match(/^\/runs\/(.+)$/)
    if (runMatch) {
      setSelectedRunId(runMatch[1])
      setCurrentView('run')
      return
    }

    // Check for group page
    const groupMatch = path.match(/^\/groups\/(.+)$/)
    if (groupMatch) {
      setSelectedGroupId(groupMatch[1])
      setCurrentView('group')
      return
    }

    // Default to dashboard
    setCurrentView('dashboard')
  }, [])

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
    // Reset to dashboard view on login
    setCurrentView('dashboard')
    setSelectedGroupId(null)
    setSelectedRunId(null)
    setInviteToken(null)
    window.history.pushState({}, '', '/')
  }

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      })
      setUser(null)
      // Reset to dashboard view on logout
      setCurrentView('dashboard')
      setSelectedGroupId(null)
      setSelectedRunId(null)
      setInviteToken(null)
      window.history.pushState({}, '', '/')
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  const handleGroupSelect = (groupId: string) => {
    setSelectedGroupId(groupId)
    setCurrentView('group')
    window.history.pushState({}, '', `/groups/${groupId}`)
  }

  const handleBackToDashboard = () => {
    setCurrentView('dashboard')
    setSelectedGroupId(null)
    setSelectedRunId(null)
    setSelectedProductId(null)
    window.history.pushState({}, '', '/')
  }

  const handleProductSelect = (productId: string) => {
    setSelectedProductId(productId)
    setCurrentView('product')
    window.history.pushState({}, '', `/products/${productId}`)
  }

  const handleRunSelect = (runId: string) => {
    setSelectedRunId(runId)
    setCurrentView('run')
    window.history.pushState({}, '', `/runs/${runId}`)
  }

  const handleBackToGroup = (groupId?: string) => {
    // If groupId is provided (e.g., from RunPage), use it
    // Otherwise fall back to selectedGroupId
    const targetGroupId = groupId || selectedGroupId

    if (targetGroupId) {
      setSelectedGroupId(targetGroupId)
      setCurrentView('group')
      setSelectedRunId(null)
      window.history.pushState({}, '', `/groups/${targetGroupId}`)
    } else {
      // Fallback to dashboard if no group ID available
      handleBackToDashboard()
    }
  }

  const handleJoinSuccess = () => {
    setCurrentView('dashboard')
    setInviteToken(null)
    window.history.pushState({}, '', '/')
  }

  const handleShoppingSelect = (runId: string) => {
    setSelectedRunId(runId)
    setCurrentView('shopping')
    window.history.pushState({}, '', `/shopping/${runId}`)
  }

  const handleBackToRun = () => {
    setCurrentView('run')
    if (selectedRunId) {
      window.history.pushState({}, '', `/runs/${selectedRunId}`)
    }
  }

  const handleDistributionSelect = (runId: string) => {
    setSelectedRunId(runId)
    setCurrentView('distribution')
    window.history.pushState({}, '', `/distribution/${runId}`)
  }

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

  // Show join page if invite link
  if (currentView === 'join' && inviteToken) {
    if (!user) {
      return <Login onLogin={handleLogin} />
    }
    return <JoinGroup inviteToken={inviteToken} onJoinSuccess={handleJoinSuccess} />
  }

  // Show login page if not authenticated
  if (!user) {
    return <Login onLogin={handleLogin} />
  }

  // Show main app if authenticated
  console.log('🔵 App: Rendering main app. currentView:', currentView, 'user:', user)

  return (
    <div className="app">
      <header>
        <h1 onClick={handleBackToDashboard} style={{ cursor: 'pointer' }}>Bulq 📦</h1>

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
                    handleProductSelect(product.id)
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
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </header>

      <main className={currentView === 'dashboard' ? 'dashboard' : ''}>
        {currentView === 'dashboard' && (
          <ErrorBoundary>
            <Groups onGroupSelect={handleGroupSelect} onRunSelect={handleRunSelect} onProductSelect={handleProductSelect} />
          </ErrorBoundary>
        )}

        {currentView === 'group' && selectedGroupId && (
          <ErrorBoundary>
            <GroupPage
              groupId={selectedGroupId}
              onBack={handleBackToDashboard}
              onRunSelect={handleRunSelect}
            />
          </ErrorBoundary>
        )}

        {currentView === 'run' && selectedRunId && (
          <ErrorBoundary>
            <RunPage
              runId={selectedRunId}
              onBack={handleBackToGroup}
              onShoppingSelect={handleShoppingSelect}
              onDistributionSelect={handleDistributionSelect}
            />
          </ErrorBoundary>
        )}

        {currentView === 'shopping' && selectedRunId && (
          <ErrorBoundary>
            <ShoppingPage
              runId={selectedRunId}
              onBack={handleBackToRun}
            />
          </ErrorBoundary>
        )}

        {currentView === 'distribution' && selectedRunId && (
          <ErrorBoundary>
            <DistributionPage
              runId={selectedRunId}
              onBack={handleBackToRun}
            />
          </ErrorBoundary>
        )}

        {currentView === 'product' && selectedProductId && (
          <ErrorBoundary>
            <ProductPage
              productId={selectedProductId}
              onBack={handleBackToDashboard}
            />
          </ErrorBoundary>
        )}
      </main>
    </div>
  )
}

export default App
