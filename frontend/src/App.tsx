import { useState, useEffect } from 'react'
import './App.css'
import Login from './components/Login'
import Groups from './components/Groups'
import GroupPage from './components/GroupPage'

interface BackendResponse {
  message: string
}

interface HealthResponse {
  status: string
}

interface User {
  id: string
  name: string
  email: string
}

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [backendMessage, setBackendMessage] = useState<string>('')
  const [healthStatus, setHealthStatus] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [currentView, setCurrentView] = useState<'dashboard' | 'group'>('dashboard')
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null)

  const BACKEND_URL = 'http://localhost:8000'

  // Check if user is already logged in
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/auth/me`, {
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
        const helloResponse = await fetch(`${BACKEND_URL}/`)
        if (!helloResponse.ok) {
          throw new Error(`HTTP error! status: ${helloResponse.status}`)
        }
        const helloData: BackendResponse = await helloResponse.json()
        setBackendMessage(helloData.message)

        // Test health endpoint
        const healthResponse = await fetch(`${BACKEND_URL}/health`)
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
      await fetch(`${BACKEND_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      })
      setUser(null)
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  const handleGroupSelect = (groupId: string) => {
    setSelectedGroupId(groupId)
    setCurrentView('group')
  }

  const handleBackToDashboard = () => {
    setCurrentView('dashboard')
    setSelectedGroupId(null)
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
        <h1>Bulq - Bulk Buying Platform</h1>
        <div className="user-info">
          <span>Welcome 1, {user.name}!</span>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </header>

      <main>
        <div style={{backgroundColor: 'yellow', padding: '10px', margin: '10px 0'}}>
          🔍 DEBUG: currentView = {currentView}
        </div>

        {currentView === 'dashboard' && (
          <>
            <div style={{backgroundColor: 'lightblue', padding: '10px', margin: '10px 0'}}>
              🔍 DEBUG: About to render Groups component
            </div>
            <Groups onGroupSelect={handleGroupSelect} />

            <div className="status-card">
              <h3>Backend Connection Test</h3>

              {loading && <p>Connecting to backend...</p>}

              {error && (
                <div className="error">
                  <p>❌ Backend connection failed: {error}</p>
                  <p>Make sure the backend is running on {BACKEND_URL}</p>
                </div>
              )}

              {!loading && !error && (
                <div className="success">
                  <p>✅ Backend connected successfully!</p>
                  <p><strong>Message:</strong> {backendMessage}</p>
                  <p><strong>Health Status:</strong> {healthStatus}</p>
                </div>
              )}
            </div>

            <div className="info-card">
              <h3>User Info</h3>
              <p><strong>Name:</strong> {user.name}</p>
              <p><strong>Email:</strong> {user.email}</p>
              <p><strong>User ID:</strong> {user.id}</p>
            </div>

            <div className="info-card">
              <h3>Development Info</h3>
              <p>Frontend: React + TypeScript + Vite</p>
              <p>Backend: FastAPI (Python)</p>
              <p>Backend URL: {BACKEND_URL}</p>
            </div>
          </>
        )}

        {currentView === 'group' && selectedGroupId && (
          <GroupPage
            groupId={selectedGroupId}
            onBack={handleBackToDashboard}
          />
        )}
      </main>
    </div>
  )
}

export default App
