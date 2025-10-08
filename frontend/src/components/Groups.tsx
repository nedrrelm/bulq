import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import './Groups.css'
import { WS_BASE_URL } from '../config'
import { groupsApi, ApiError } from '../api'
import type { Group } from '../api'
import type { ProductSearchResult } from '../types/product'
import NewGroupPopup from './NewGroupPopup'
import ErrorBoundary from './ErrorBoundary'
import { useWebSocket } from '../hooks/useWebSocket'
import { getStateLabel } from '../utils/runStates'

// Using Group type from API layer

interface GroupsProps {
  onGroupSelect: (groupId: string) => void
  onRunSelect: (runId: string) => void
}

export default function Groups({ onGroupSelect, onRunSelect }: GroupsProps) {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showNewGroupPopup, setShowNewGroupPopup] = useState(false)

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        setLoading(true)
        setError('')

        const groupsData = await groupsApi.getMyGroups()
        setGroups(groupsData)
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Failed to load groups')
      } finally {
        setLoading(false)
      }
    }

    fetchGroups()
  }, [])

  // Track current group IDs to avoid reconnecting when group data changes
  const groupIdsRef = useRef<string>('')
  const wsConnectionsRef = useRef<WebSocket[]>([])

  // WebSocket connections for real-time updates - one per group
  // Memoize group IDs to avoid unnecessary reconnections
  const groupIds = useMemo(() => groups.map(g => g.id).join(','), [groups])

  useEffect(() => {
    if (groups.length === 0) {
      // Clean up any existing connections
      wsConnectionsRef.current.forEach(ws => {
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close()
        }
      })
      wsConnectionsRef.current = []
      return
    }

    // Only recreate connections if group IDs actually changed
    if (groupIdsRef.current === groupIds) {
      return
    }

    // Clean up old connections before creating new ones
    wsConnectionsRef.current.forEach(ws => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close()
      }
    })
    wsConnectionsRef.current = []

    groupIdsRef.current = groupIds

    groups.forEach((group) => {
      const ws = new WebSocket(`${WS_BASE_URL}/ws/groups/${group.id}`)

      ws.onopen = () => {
        // Connection established
      }

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

      ws.onerror = (error) => {
        // Only log errors if the connection isn't intentionally closing
        if (ws.readyState !== WebSocket.CLOSING && ws.readyState !== WebSocket.CLOSED) {
          console.error(`WebSocket error for group ${group.id}:`, error)
        }
      }

      ws.onclose = () => {
        // Connection closed
      }

      wsConnectionsRef.current.push(ws)
    })

    // Cleanup on unmount
    return () => {
      wsConnectionsRef.current.forEach(ws => {
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close()
        }
      })
      wsConnectionsRef.current = []
    }
  }, [groupIds, groups]) // Only run when group IDs change, not when group data changes

  const handleGroupClick = (groupId: string) => {
    onGroupSelect(groupId)
  }

  const handleNewGroupSuccess = (newGroup: Group) => {
    setShowNewGroupPopup(false)
    // Add the new group to the list optimistically
    setGroups(prev => [...prev, newGroup])
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
            <ErrorBoundary key={group.id}>
              <div
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
            </ErrorBoundary>
          ))}
        </div>
      )}
    </div>
    </>
  )
}