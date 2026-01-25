import { useCallback, lazy, Suspense } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import '../styles/components/GroupPage.css'
import { WS_BASE_URL } from '../config'
import ErrorBoundary from './ErrorBoundary'

// Lazy load popup components for better code splitting
const NewRunPopup = lazy(() => import('./NewRunPopup'))
import { useWebSocket } from '../hooks/useWebSocket'
import { useAuth } from '../contexts/AuthContext'
import Toast from './Toast'
import ConfirmDialog from './ConfirmDialog'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { useModal } from '../hooks/useModal'
import RunCard from './RunCard'
import { useGroup, useGroupRuns, groupKeys } from '../hooks/queries'
import { getErrorMessage } from '../utils/errorHandling'

type RunSummary = {
  id: string
  store_name: string
  state: string
  leader_name: string
  leader_is_removed: boolean
  planned_on: string | null
  planning_at: string | null
  active_at: string | null
  confirmed_at: string | null
  shopping_at: string | null
  adjusting_at: string | null
  distributing_at: string | null
  completed_at: string | null
  cancelled_at: string | null
}

export default function GroupPage() {
  const { t } = useTranslation(['group'])
  const { groupId } = useParams<{ groupId: string }>()
  const navigate = useNavigate()

  // Redirect if no groupId
  if (!groupId) {
    navigate('/')
    return null
  }
  // Use React Query for data fetching
  const { data: group, isLoading: groupLoading, error: groupError } = useGroup(groupId)
  const { data: runs = [], isLoading: runsLoading, error: runsError } = useGroupRuns(groupId)
  const queryClient = useQueryClient()

  const loading = groupLoading || runsLoading
  const error = groupError ? getErrorMessage(groupError, '') : runsError ? getErrorMessage(runsError, '') : ''

  const newRunModal = useModal()
  const { toast, showToast, hideToast } = useToast()
  const { confirmState, hideConfirm, handleConfirm } = useConfirm()
  const { user } = useAuth()

  // WebSocket for real-time updates
  const handleWebSocketMessage = useCallback((message: { type: string; data: unknown }) => {
    const messageData = message.data as { run_id?: string; removed_user_id?: string }

    if (message.type === 'run_created') {
      // Invalidate runs query to refetch with new run
      queryClient.invalidateQueries({ queryKey: groupKeys.runs(groupId) })
    } else if (message.type === 'run_state_changed' || message.type === 'run_cancelled') {
      // Invalidate runs query to update run state
      queryClient.invalidateQueries({ queryKey: groupKeys.runs(groupId) })
      // Also invalidate the specific run
      if (messageData.run_id) {
        queryClient.invalidateQueries({ queryKey: ['runs', 'detail', messageData.run_id] })
      }
    } else if (message.type === 'member_removed') {
      // If current user was removed, redirect to main page
      if (user && messageData.removed_user_id === user.id) {
        showToast(t('group:messages.removed'), 'error')
        setTimeout(() => {
          navigate('/')
        }, 1500)
        return
      }

      // Refresh the runs list to get updated leader_is_removed status
      queryClient.invalidateQueries({ queryKey: groupKeys.runs(groupId) })
      queryClient.invalidateQueries({ queryKey: groupKeys.detail(groupId) })
    }
  }, [groupId, user, showToast, queryClient, navigate])

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
    .filter((run: RunSummary) => !['completed', 'cancelled'].includes(run.state))
    .sort((a: RunSummary, b: RunSummary) => (stateOrder[b.state] || 0) - (stateOrder[a.state] || 0))

  const completedRuns = runs
    .filter((run: RunSummary) => run.state === 'completed')
    .sort((a: RunSummary, b: RunSummary) => {
      const dateA = a.completed_at || ''
      const dateB = b.completed_at || ''
      return dateB.localeCompare(dateA) // Latest first
    })

  const cancelledRuns = runs
    .filter((run: RunSummary) => run.state === 'cancelled')
    .sort((a: RunSummary, b: RunSummary) => {
      const dateA = a.cancelled_at || ''
      const dateB = b.cancelled_at || ''
      return dateB.localeCompare(dateA) // Latest first
    })

  const handleNewRunClick = () => {
    newRunModal.open()
  }

  const handleNewRunSuccess = () => {
    newRunModal.close()
    // WebSocket will update the runs list automatically
  }

  const handleRunClick = (runId: string) => {
    navigate(`/runs/${runId}`)
  }

  const handleManageClick = () => {
    navigate(`/groups/${groupId}/manage`)
  }

  return (
    <div className="group-page">
      <Suspense fallback={null}>
        {newRunModal.isOpen && (
          <NewRunPopup
            groupId={groupId}
            onClose={newRunModal.close}
            onSuccess={handleNewRunSuccess}
          />
        )}
      </Suspense>

      <div className="breadcrumb">
        <span className="breadcrumb-link" onClick={() => navigate('/')}>
          {group?.name || t('group:loading')}
        </span>
      </div>

      <div className="group-actions">
        <button onClick={handleNewRunClick} className="new-run-button">
          {t('group:actions.newRun')}
        </button>
        <button onClick={handleManageClick} className="btn btn-secondary">
          {t('group:actions.manageGroup')}
        </button>
      </div>

      {loading && <p>{t('group:loading')}</p>}

      {error && (
        <div className="error">
          <p>{t('group:errors.loadFailed')}: {error}</p>
        </div>
      )}

      {!loading && !error && (
        <>
          <div className="runs-section">
            <h3>{t('group:sections.currentRuns')} ({currentRuns.length})</h3>
            {currentRuns.length === 0 ? (
              <div className="no-runs">
                <p>{t('group:empty.noCurrentRuns')}</p>
              </div>
            ) : (
              <div className="runs-list">
                {currentRuns.map((run: RunSummary) => (
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
            <h3>{t('group:sections.completedRuns')} ({completedRuns.length})</h3>
            {completedRuns.length === 0 ? (
              <div className="no-runs">
                <p>{t('group:empty.noCompletedRuns')}</p>
              </div>
            ) : (
              <div className="runs-list">
                {completedRuns.map((run: RunSummary) => (
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
            <h3>{t('group:sections.cancelledRuns')} ({cancelledRuns.length})</h3>
            {cancelledRuns.length === 0 ? (
              <div className="no-runs">
                <p>{t('group:empty.noCancelledRuns')}</p>
              </div>
            ) : (
              <div className="runs-list">
                {cancelledRuns.map((run: RunSummary) => (
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