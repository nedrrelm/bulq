import { useState, useEffect } from 'react'
import './App.css'

interface BackendResponse {
  message: string
}

interface HealthResponse {
  status: string
}

function App() {
  const [backendMessage, setBackendMessage] = useState<string>('')
  const [healthStatus, setHealthStatus] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  const BACKEND_URL = 'http://localhost:8000'

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

  return (
    <div className="app">
      <header>
        <h1>Bulq - Bulk Buying Platform</h1>
        <h2>Frontend Status</h2>
      </header>

      <main>
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
          <h3>Development Info</h3>
          <p>Frontend: React + TypeScript + Vite</p>
          <p>Backend: FastAPI (Python)</p>
          <p>Backend URL: {BACKEND_URL}</p>
        </div>
      </main>
    </div>
  )
}

export default App
