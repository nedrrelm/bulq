import { useState, useEffect } from 'react'
import './GroupPage.css'

interface Run {
  id: string
  group_id: string
  store_id: string
  store_name: string
  state: string
}

interface GroupPageProps {
  groupId: string
  onBack: () => void
}

export default function GroupPage({ groupId, onBack }: GroupPageProps) {
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const BACKEND_URL = 'http://localhost:8000'

  useEffect(() => {
    const fetchRuns = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${BACKEND_URL}/groups/${groupId}/runs`, {
          credentials: 'include'
        })

        if (!response.ok) {
          const errorText = await response.text()
          throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
        }

        const runsData: Run[] = await response.json()
        setRuns(runsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load runs')
      } finally {
        setLoading(false)
      }
    }

    fetchRuns()
  }, [groupId])

  const getStateDisplay = (state: string) => {
    switch (state) {
      case 'planning':
        return { label: 'Planning', color: '#fbbf24' }
      case 'active':
        return { label: 'Active', color: '#10b981' }
      case 'confirmed':
        return { label: 'Confirmed', color: '#3b82f6' }
      case 'shopping':
        return { label: 'Shopping', color: '#8b5cf6' }
      case 'completed':
        return { label: 'Completed', color: '#6b7280' }
      case 'cancelled':
        return { label: 'Cancelled', color: '#ef4444' }
      default:
        return { label: state, color: '#6b7280' }
    }
  }

  const currentRuns = runs.filter(run => !['completed', 'cancelled'].includes(run.state))
  const pastRuns = runs.filter(run => ['completed', 'cancelled'].includes(run.state))

  const handleNewRunClick = () => {
    // TODO: Implement new run functionality
    alert('New run functionality will be implemented soon!')
  }

  return (
    <div className="group-page">
      <div className="group-header">
        <button onClick={onBack} className="back-button">
          ← Back to Dashboard
        </button>
        <h2>Group Runs</h2>
        <button onClick={handleNewRunClick} className="new-run-button">
          + New Run
        </button>
      </div>

      {loading && <p>Loading runs...</p>}

      {error && (
        <div className="error">
          <p>❌ Failed to load runs: {error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          <div className="runs-section">
            <h3>Current Runs ({currentRuns.length})</h3>
            {currentRuns.length === 0 ? (
              <div className="no-runs">
                <p>No current runs. Click "New Run" to start one!</p>
              </div>
            ) : (
              <div className="runs-list">
                {currentRuns.map((run) => {
                  const stateDisplay = getStateDisplay(run.state)
                  return (
                    <div key={run.id} className="run-item">
                      <div className="run-header">
                        <h4>{run.store_name}</h4>
                        <span
                          className="run-state"
                          style={{
                            backgroundColor: stateDisplay.color,
                            color: 'white',
                            padding: '4px 12px',
                            borderRadius: '12px',
                            fontSize: '0.875rem',
                            fontWeight: 'bold'
                          }}
                        >
                          {stateDisplay.label}
                        </span>
                      </div>
                      <p className="run-id">ID: {run.id}</p>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          <div className="runs-section">
            <h3>Past Runs ({pastRuns.length})</h3>
            {pastRuns.length === 0 ? (
              <div className="no-runs">
                <p>No past runs yet.</p>
              </div>
            ) : (
              <div className="runs-list">
                {pastRuns.map((run) => {
                  const stateDisplay = getStateDisplay(run.state)
                  return (
                    <div key={run.id} className="run-item past">
                      <div className="run-header">
                        <h4>{run.store_name}</h4>
                        <span
                          className="run-state"
                          style={{
                            backgroundColor: stateDisplay.color,
                            color: 'white',
                            padding: '4px 12px',
                            borderRadius: '12px',
                            fontSize: '0.875rem',
                            fontWeight: 'bold'
                          }}
                        >
                          {stateDisplay.label}
                        </span>
                      </div>
                      <p className="run-id">ID: {run.id}</p>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}