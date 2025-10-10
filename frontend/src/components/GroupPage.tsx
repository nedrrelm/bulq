import { useState, useEffect, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import '../styles/components/GroupPage.css'
import { WS_BASE_URL } from '../config'
import { ApiError } from '../api'
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
import { useGroup, useGroupRuns, groupKeys } from '../hooks/queries'

// Using GroupDetails type from API layer
type Run = GroupDetails['runs'][0]

interface GroupPageProps {
  groupId: string
  onBack: () => void
  onRunSelect: (runId: string) => void
  onManageSelect?: (groupId: string) => void
}

export default function GroupPage({ groupId, onBack, onRunSelect, onManageSelect }: GroupPageProps) {
  // Use React Query for data fetching
  const { data: group, isLoading: groupLoading, error: groupError } = useGroup(groupId)
  const { data: runs = [], isLoading: runsLoading, error: runsError } = useGroupRuns(groupId)
  const queryClient = useQueryClient()

  const loading = groupLoading || runsLoading
  const error = groupError instanceof Error ? groupError.message : runsError instanceof Error ? runsError.message : ''

  const newRunModal = useModal()
  const { toast, showToast, hideToast } = useToast()
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()
  const { user } = useAuth()

  // WebSocket for real-time updates
  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'run_created') {
      // Invalidate runs query to refetch with new run
      queryClient.invalidateQueries({ queryKey: groupKeys.runs(groupId) })
    } else if (message.type === 'run_state_changed' || message.type === 'run_cancelled') {
      // Invalidate runs query to update run state
      queryClient.invalidateQueries({ queryKey: groupKeys.runs(groupId) })
      // Also invalidate the specific run
      if (message.data.run_id) {
        queryClient.invalidateQueries({ queryKey: ['runs', 'detail', message.data.run_id] })
      }
    } else if (message.type === 'member_removed') {
      // If current user was removed, redirect to main page
      if (user && message.data.removed_user_id === user.id) {
        showToast('You have been removed from this group', 'error')
        setTimeout(() => {
          window.location.href = '/'
        }, 1500)
        return
      }

      // Refresh the runs list to get updated leader_is_removed status
      queryClient.invalidateQueries({ queryKey: groupKeys.runs(groupId) })
      queryClient.invalidateQueries({ queryKey: groupKeys.detail(groupId) })
    }
  }, [groupId, user, showToast, queryClient])

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