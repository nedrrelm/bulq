import { useState, useEffect, useCallback } from 'react'
import './GroupPage.css'
import { WS_BASE_URL } from '../config'
import { groupsApi, ApiError } from '../api'
import type { GroupDetails } from '../api'
import NewRunPopup from './NewRunPopup'
import ErrorBoundary from './ErrorBoundary'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAuth } from '../contexts/AuthContext'
import { getStateLabel } from '../utils/runStates'
import Toast from './Toast'
import ConfirmDialog from './ConfirmDialog'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { useModal } from '../hooks/useModal'
import RunCard from './RunCard'

// Using GroupDetails type from API layer
type Run = GroupDetails['runs'][0]

interface GroupPageProps {
  groupId: string
  onBack: () => void
  onRunSelect: (runId: string) => void
  onManageSelect?: (groupId: string) => void
}

export default function GroupPage({ groupId, onBack, onRunSelect, onManageSelect }: GroupPageProps) {
  const [runs, setRuns] = useState<Run[]>([])
  const [group, setGroup] = useState<GroupDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const newRunModal = useModal()
  const { toast, showToast, hideToast } = useToast()
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()
  const { user } = useAuth()

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
  const handleWebSocketMessage = useCallback((message: any) => {
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
    } else if (message.type === 'run_state_changed' || message.type === 'run_cancelled') {
      // Update run state
      setRuns(prev => prev.map(run =>
        run.id === message.data.run_id
          ? { ...run, state: message.data.new_state || message.data.state }
          : run
      ))
    } else if (message.type === 'member_removed') {
      // If current user was removed, redirect to main page
      if (user && message.data.removed_user_id === user.id) {
        showToast('You have been removed from this group', 'error')
        setTimeout(() => {
          window.location.href = '/'
        }, 1500)
      }
    }
  }, [groupId, user, showToast])

  useWebSocket(
    groupId ? `${WS_BASE_URL}/ws/groups/${groupId}` : null,
    {
      onMessage: handleWebSocketMessage
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

  const completedRuns = runs.filter(run => run.state === 'completed')
  const cancelledRuns = runs.filter(run => run.state === 'cancelled')

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

  const handleManageClick = () => {
    if (onManageSelect) {
      onManageSelect(groupId)
    }
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
        <button onClick={handleManageClick} className="btn btn-secondary">
          ⚙️ Manage Group
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
                {currentRuns.map((run) => (
                  <ErrorBoundary key={run.id}>
                    <RunCard
                      run={run}
                      onClick={handleRunClick}
                      showAsLink={false}
                    />
                  </ErrorBoundary>
                ))}
              </div>
            )}
          </div>

          <div className="runs-section">
            <h3>Completed Runs ({completedRuns.length})</h3>
            {completedRuns.length === 0 ? (
              <div className="no-runs">
                <p>No completed runs yet.</p>
              </div>
            ) : (
              <div className="runs-list">
                {completedRuns.map((run) => (
                  <ErrorBoundary key={run.id}>
                    <RunCard
                      run={run}
                      onClick={handleRunClick}
                      showAsLink={false}
                    />
                  </ErrorBoundary>
                ))}
              </div>
            )}
          </div>

          <div className="runs-section">
            <h3>Cancelled Runs ({cancelledRuns.length})</h3>
            {cancelledRuns.length === 0 ? (
              <div className="no-runs">
                <p>No cancelled runs.</p>
              </div>
            ) : (
              <div className="runs-list">
                {cancelledRuns.map((run) => (
                  <ErrorBoundary key={run.id}>
                    <RunCard
                      run={run}
                      onClick={handleRunClick}
                      showAsLink={false}
                    />
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