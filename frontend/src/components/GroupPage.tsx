import { useState, useEffect } from 'react'
import './GroupPage.css'
import { API_BASE_URL, WS_BASE_URL } from '../config'
import NewRunPopup from './NewRunPopup'
import ErrorBoundary from './ErrorBoundary'
import { useWebSocket } from '../hooks/useWebSocket'

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
  invite_token: string
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
  const [showNewRunPopup, setShowNewRunPopup] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError('')

        // Fetch group details
        const groupResponse = await fetch(`${API_BASE_URL}/groups/${groupId}`, {
          credentials: 'include'
        })

        if (!groupResponse.ok) {
          const errorText = await groupResponse.text()
          throw new Error(`HTTP error! status: ${groupResponse.status} - ${errorText}`)
        }

        const groupData: Group = await groupResponse.json()
        setGroup(groupData)

        // Fetch runs
        const runsResponse = await fetch(`${API_BASE_URL}/groups/${groupId}/runs`, {
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

  // WebSocket for real-time updates
  useWebSocket(
    groupId ? `${WS_BASE_URL}/ws/groups/${groupId}` : null,
    {
      onMessage: (message) => {
        if (message.type === 'run_created') {
          // Check if run already exists (to avoid duplicates from handleNewRunSuccess)
          setRuns(prev => {
            if (prev.some(run => run.id === message.data.run_id)) {
              return prev
            }
            const newRun: Run = {
              id: message.data.run_id,
              group_id: groupId,
              store_id: message.data.store_id,
              store_name: message.data.store_name,
              state: message.data.state
            }
            return [newRun, ...prev]
          })
        } else if (message.type === 'run_state_changed') {
          // Update run state
          setRuns(prev => prev.map(run =>
            run.id === message.data.run_id
              ? { ...run, state: message.data.new_state }
              : run
          ))
        }
      }
    }
  )

  const getStateLabel = (state: string) => {
    switch (state) {
      case 'planning':
        return 'Planning'
      case 'active':
        return 'Active'
      case 'confirmed':
        return 'Confirmed'
      case 'shopping':
        return 'Shopping'
      case 'adjusting':
        return 'Adjusting'
      case 'distributing':
        return 'Distributing'
      case 'completed':
        return 'Completed'
      case 'cancelled':
        return 'Cancelled'
      default:
        return state
    }
  }

  // State ordering for sorting (reverse order: distributing > adjusting > shopping > confirmed > active > planning)
  const stateOrder: Record<string, number> = {
    'distributing': 6,
    'adjusting': 5,
    'shopping': 4,
    'confirmed': 3,
    'active': 2,
    'planning': 1
  }

  const currentRuns = runs
    .filter(run => !['completed', 'cancelled'].includes(run.state))
    .sort((a, b) => (stateOrder[b.state] || 0) - (stateOrder[a.state] || 0))

  const pastRuns = runs.filter(run => ['completed', 'cancelled'].includes(run.state))

  const handleNewRunClick = () => {
    setShowNewRunPopup(true)
  }

  const handleNewRunSuccess = () => {
    setShowNewRunPopup(false)
    // Refresh the runs list
    const fetchRuns = async () => {
      try {
        const runsResponse = await fetch(`${API_BASE_URL}/groups/${groupId}/runs`, {
          credentials: 'include'
        })
        if (runsResponse.ok) {
          const runsData: Run[] = await runsResponse.json()
          setRuns(runsData)
        }
      } catch (err) {
        console.error('Failed to refresh runs:', err)
      }
    }
    fetchRuns()
  }

  const handleRunClick = (runId: string) => {
    onRunSelect(runId)
  }

  const handleCopyInviteLink = () => {
    if (!group) return
    const inviteUrl = `${window.location.origin}/invite/${group.invite_token}`
    navigator.clipboard.writeText(inviteUrl)
      .then(() => {
        alert('Invite link copied to clipboard!')
      })
      .catch(err => {
        console.error('Failed to copy:', err)
        alert('Failed to copy invite link')
      })
  }

  const handleRegenerateToken = async () => {
    if (!group) return
    if (!confirm('Are you sure you want to regenerate the invite link? The old link will stop working.')) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/groups/${groupId}/regenerate-invite`, {
        method: 'POST',
        credentials: 'include'
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to regenerate invite token')
      }

      const data = await response.json()
      setGroup({ ...group, invite_token: data.invite_token })
      alert('Invite link regenerated successfully!')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to regenerate invite link')
    }
  }

  return (
    <div className="group-page">
      {showNewRunPopup && (
        <NewRunPopup
          groupId={groupId}
          onClose={() => setShowNewRunPopup(false)}
          onSuccess={handleNewRunSuccess}
        />
      )}

      <div className="breadcrumb">
        <span style={{ cursor: 'pointer', color: '#667eea' }} onClick={onBack}>
          {group?.name || 'Loading...'}
        </span>
      </div>

      <div className="group-actions">
        <button onClick={handleNewRunClick} className="new-run-button">
          + New Run
        </button>
        <div className="invite-actions">
          <button onClick={handleCopyInviteLink} className="btn btn-secondary">
            📋 Copy Invite Link
          </button>
          <button onClick={handleRegenerateToken} className="btn btn-secondary">
            🔄 Regenerate Link
          </button>
        </div>
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
                {currentRuns.map((run) => (
                  <ErrorBoundary key={run.id}>
                    <div
                      className="run-item"
                      onClick={() => handleRunClick(run.id)}
                    >
                      <div className="run-header">
                        <h4>{run.store_name}</h4>
                        <span className={`run-state state-${run.state}`}>
                          {getStateLabel(run.state)}
                        </span>
                      </div>
                      <p className="run-id">ID: {run.id}</p>
                    </div>
                  </ErrorBoundary>
                ))}
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
                {pastRuns.map((run) => (
                  <ErrorBoundary key={run.id}>
                    <div
                      className="run-item past"
                      onClick={() => handleRunClick(run.id)}
                    >
                      <div className="run-header">
                        <h4>{run.store_name}</h4>
                      <span className={`run-state state-${run.state}`}>
                        {getStateLabel(run.state)}
                      </span>
                    </div>
                    <p className="run-id">ID: {run.id}</p>
                  </div>
                  </ErrorBoundary>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}