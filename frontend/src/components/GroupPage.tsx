import { useState, useEffect } from 'react'
import './GroupPage.css'

interface Run {
  id: string
  group_id: string
  store_id: string
  store_name: string
  state: string
}

interface Group {
  id: string
  name: string
}

interface GroupPageProps {
  groupId: string
  onBack: () => void
  onRunSelect: (runId: string) => void
}

export default function GroupPage({ groupId, onBack, onRunSelect }: GroupPageProps) {
  const [runs, setRuns] = useState<Run[]>([])
  const [group, setGroup] = useState<Group | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const BACKEND_URL = 'http://localhost:8000'

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError('')

        // Fetch group details
        const groupResponse = await fetch(`${BACKEND_URL}/groups/${groupId}`, {
          credentials: 'include'
        })

        if (!groupResponse.ok) {
          const errorText = await groupResponse.text()
          throw new Error(`HTTP error! status: ${groupResponse.status} - ${errorText}`)
        }

        const groupData: Group = await groupResponse.json()
        setGroup(groupData)

        // Fetch runs
        const runsResponse = await fetch(`${BACKEND_URL}/groups/${groupId}/runs`, {
          credentials: 'include'
        })

        if (!runsResponse.ok) {
          const errorText = await runsResponse.text()
          throw new Error(`HTTP error! status: ${runsResponse.status} - ${errorText}`)
        }

        const runsData: Run[] = await runsResponse.json()
        setRuns(runsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
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

  const handleRunClick = (runId: string) => {
    onRunSelect(runId)
  }

  return (
    <div className="group-page">
      <div className="breadcrumb">
        {group?.name || 'Loading...'}
      </div>

      <button onClick={handleNewRunClick} className="new-run-button">
        + New Run
      </button>

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
                    <div
                      key={run.id}
                      className="run-item"
                      onClick={() => handleRunClick(run.id)}
                    >
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
                    <div
                      key={run.id}
                      className="run-item past"
                      onClick={() => handleRunClick(run.id)}
                    >
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