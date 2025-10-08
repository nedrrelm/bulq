import { useState, useEffect } from 'react'
import './GroupPage.css'
import { WS_BASE_URL } from '../config'
import { groupsApi, ApiError } from '../api'
import type { GroupDetails } from '../api'
import NewRunPopup from './NewRunPopup'
import ErrorBoundary from './ErrorBoundary'
import { useWebSocket } from '../hooks/useWebSocket'
import { getStateLabel } from '../utils/runStates'
import Toast from './Toast'
import ConfirmDialog from './ConfirmDialog'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { useModal } from '../hooks/useModal'

// Using GroupDetails type from API layer
type Run = GroupDetails['runs'][0]

interface GroupPageProps {
  groupId: string
  onBack: () => void
  onRunSelect: (runId: string) => void
}

export default function GroupPage({ groupId, onBack, onRunSelect }: GroupPageProps) {
  const [runs, setRuns] = useState<Run[]>([])
  const [group, setGroup] = useState<GroupDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const newRunModal = useModal()
  const { toast, showToast, hideToast } = useToast()
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError('')

        // Fetch group details
        const groupData = await groupsApi.getGroup(groupId)
        setGroup(groupData)

        // Fetch runs
        const runsData = await groupsApi.getGroupRuns(groupId)
        setRuns(runsData)
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Failed to load data')
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
    newRunModal.open()
  }

  const handleNewRunSuccess = () => {
    newRunModal.close()
    // WebSocket will update the runs list automatically
  }

  const handleRunClick = (runId: string) => {
    onRunSelect(runId)
  }

  const handleCopyInviteLink = () => {
    if (!group) return
    const inviteUrl = `${window.location.origin}/invite/${group.invite_token}`
    navigator.clipboard.writeText(inviteUrl)
      .then(() => {
        showToast('Invite link copied to clipboard!', 'success')
      })
      .catch(err => {
        console.error('Failed to copy:', err)
        showToast('Failed to copy invite link', 'error')
      })
  }

  const handleRegenerateToken = async () => {
    if (!group) return

    const regenerateAction = async () => {
      try {
        const data = await groupsApi.regenerateInvite(groupId)
        setGroup({ ...group, invite_token: data.invite_token })
        showToast('Invite link regenerated successfully!', 'success')
      } catch (err) {
        showToast(err instanceof ApiError ? err.message : 'Failed to regenerate invite link', 'error')
      }
    }

    showConfirm(
      'Are you sure you want to regenerate the invite link? The old link will stop working.',
      regenerateAction,
      { danger: true }
    )
  }

  return (
    <div className="group-page">
      {newRunModal.isOpen && (
        <NewRunPopup
          groupId={groupId}
          onClose={newRunModal.close}
          onSuccess={handleNewRunSuccess}
        />
      )}

      <div className="breadcrumb">
        <span className="breadcrumb-link" onClick={onBack}>
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

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
        />
      )}

      {confirmState && (
        <ConfirmDialog
          message={confirmState.message}
          onConfirm={handleConfirm}
          onCancel={hideConfirm}
          danger={confirmState.danger}
        />
      )}
    </div>
  )
}