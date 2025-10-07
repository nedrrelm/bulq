import { useState, useEffect } from 'react'
import './Groups.css'
import NewGroupPopup from './NewGroupPopup'
import { useWebSocket } from '../hooks/useWebSocket'

interface RunSummary {
  id: string
  store_name: string
  state: string
}

interface Group {
  id: string
  name: string
  description: string
  member_count: number
  active_runs_count: number
  completed_runs_count: number
  active_runs: RunSummary[]
  created_at: string
}

interface GroupsProps {
  onGroupSelect: (groupId: string) => void
  onRunSelect: (runId: string) => void
  onProductSelect: (productId: string) => void
}

interface ProductSearchResult {
  id: string
  name: string
  store_id: string
  store_name: string
  base_price: number | null
}

export default function Groups({ onGroupSelect, onRunSelect }: GroupsProps) {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showNewGroupPopup, setShowNewGroupPopup] = useState(false)

  const BACKEND_URL = 'http://localhost:8000'

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

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${BACKEND_URL}/groups/my-groups`, {
          credentials: 'include'
        })

        if (!response.ok) {
          const errorText = await response.text()
          throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
        }

        const groupsData: Group[] = await response.json()
        setGroups(groupsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load groups')
      } finally {
        setLoading(false)
      }
    }

    fetchGroups()
  }, [])

  // WebSocket connections for real-time updates
  useEffect(() => {
    const wsConnections: any[] = []

    groups.forEach((group) => {
      const ws = new WebSocket(`ws://localhost:8000/ws/groups/${group.id}`)

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)

          if (message.type === 'run_created') {
            // Add new run to the group's active runs
            setGroups(prev => prev.map(g => {
              if (g.id === group.id) {
                const newRun: RunSummary = {
                  id: message.data.run_id,
                  store_name: message.data.store_name,
                  state: message.data.state
                }
                return {
                  ...g,
                  active_runs: [...g.active_runs, newRun],
                  active_runs_count: g.active_runs_count + 1
                }
              }
              return g
            }))
          } else if (message.type === 'run_state_changed') {
            // Update run state in active runs
            setGroups(prev => prev.map(g => {
              if (g.id === group.id) {
                // If completed, move to completed count
                if (message.data.new_state === 'completed') {
                  return {
                    ...g,
                    active_runs: g.active_runs.filter(r => r.id !== message.data.run_id),
                    active_runs_count: g.active_runs_count - 1,
                    completed_runs_count: g.completed_runs_count + 1
                  }
                }
                // Otherwise just update the state
                return {
                  ...g,
                  active_runs: g.active_runs.map(r =>
                    r.id === message.data.run_id
                      ? { ...r, state: message.data.new_state }
                      : r
                  )
                }
              }
              return g
            }))
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      wsConnections.push(ws)
    })

    // Cleanup on unmount or when groups change
    return () => {
      wsConnections.forEach(ws => ws.close())
    }
  }, [groups.map(g => g.id).join(',')]) // Re-run when group IDs change

  const handleGroupClick = (groupId: string) => {
    onGroupSelect(groupId)
  }

  const handleNewGroupSuccess = () => {
    setShowNewGroupPopup(false)
    // Refresh the groups list
    const fetchGroups = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/groups/my-groups`, {
          credentials: 'include'
        })
        if (response.ok) {
          const groupsData: Group[] = await response.json()
          setGroups(groupsData)
        }
      } catch (err) {
        console.error('Failed to refresh groups:', err)
      }
    }
    fetchGroups()
  }

  return (
    <>
      {showNewGroupPopup && (
        <NewGroupPopup
          onClose={() => setShowNewGroupPopup(false)}
          onSuccess={handleNewGroupSuccess}
        />
      )}

      <div className="groups-container">
        <div className="groups-header">
          <h3>My Groups</h3>
          <button onClick={() => setShowNewGroupPopup(true)} className="btn btn-primary">
            + New Group
          </button>
        </div>

      {loading && <p>Loading groups...</p>}

      {error && (
        <div className="error">
          <p>❌ Failed to load groups: {error}</p>
        </div>
      )}

      {!loading && !error && groups.length === 0 && (
        <div className="no-groups">
          <p>You haven't joined any groups yet.</p>
          <p>Ask a friend to invite you to their group!</p>
        </div>
      )}

      {!loading && !error && groups.length > 0 && (
        <div className="groups-list">
          {groups.map((group) => (
            <div
              key={group.id}
              className="group-item"
              onClick={() => handleGroupClick(group.id)}
            >
              <div className="group-header">
                <h4>{group.name}</h4>
              </div>
              <div className="group-stats">
                <span className="stat">
                  <span className="stat-icon">👥</span>
                  {group.member_count} {group.member_count === 1 ? 'member' : 'members'}
                </span>
                <span className="stat">
                  <span className="stat-icon">✅</span>
                  {group.completed_runs_count} completed {group.completed_runs_count === 1 ? 'run' : 'runs'}
                </span>
              </div>

              {group.active_runs.length > 0 && (
                <div className="active-runs">
                  {group.active_runs.map((run) => (
                    <div
                      key={run.id}
                      className="run-summary"
                      onClick={(e) => {
                        e.stopPropagation()
                        onRunSelect(run.id)
                      }}
                    >
                      <span className="run-store">{run.store_name}</span>
                      <span className={`run-state state-${run.state}`}>{getStateLabel(run.state)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
    </>
  )
}