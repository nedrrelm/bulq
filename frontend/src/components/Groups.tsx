import { useState, useEffect, useCallback, lazy, Suspense } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import '../styles/components/Groups.css'
import { WS_BASE_URL } from '../config'
import { reassignmentApi } from '../api'
import type { Group, Store } from '../api'
import type { PendingReassignments } from '../types'
import type { WebSocketMessage } from '../types/websocket'
import GroupItem from './GroupItem'
import { useWebSocket } from '../hooks/useWebSocket'
import { useGroups, groupKeys } from '../hooks/queries'
import { getErrorMessage } from '../utils/errorHandling'
import { logger } from '../utils/logger'

// Lazy load popup components for better code splitting
const NewGroupPopup = lazy(() => import('./NewGroupPopup'))
const NewStorePopup = lazy(() => import('./NewStorePopup'))
const NewProductPopup = lazy(() => import('./NewProductPopup'))

// Using Group type from API layer

interface GroupsProps {
  onGroupSelect: (groupId: string) => void
  onRunSelect: (runId: string) => void
}

export default function Groups({ onGroupSelect, onRunSelect }: GroupsProps) {
  const { t } = useTranslation(['groups', 'common'])
  // Use React Query for groups data
  const { data: groups = [], isLoading: loading, error: queryError } = useGroups()
  const queryClient = useQueryClient()

  const [showNewGroupPopup, setShowNewGroupPopup] = useState(false)
  const [showNewStorePopup, setShowNewStorePopup] = useState(false)
  const [showNewProductPopup, setShowNewProductPopup] = useState(false)
  const [pendingReassignments, setPendingReassignments] = useState<PendingReassignments>({ sent: [], received: [] })

  // Convert React Query error to string
  const error = getErrorMessage(queryError, '')

  useEffect(() => {
    const fetchReassignments = async () => {
      try {
        const requests = await reassignmentApi.getMyRequests()
        setPendingReassignments(requests)
      } catch (err) {
        logger.error('Failed to fetch reassignment requests:', err)
      }
    }

    fetchReassignments()
  }, [])

  // WebSocket connection for real-time updates - single user connection
  // This replaces the previous multiple group-specific connections
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'run_created') {
      // Invalidate groups query to refetch with new run
      queryClient.invalidateQueries({ queryKey: groupKeys.list() })
      // Also invalidate the specific group's runs if group_id is provided
      const data = message.data as { group_id?: string }
      if (data.group_id) {
        queryClient.invalidateQueries({ queryKey: groupKeys.runs(data.group_id) })
      }
    } else if (message.type === 'run_state_changed') {
      // Invalidate groups query to update run states
      queryClient.invalidateQueries({ queryKey: groupKeys.list() })
      // Also invalidate the specific group's runs and the run itself
      const data = message.data as { group_id?: string; run_id?: string }
      if (data.group_id) {
        queryClient.invalidateQueries({ queryKey: groupKeys.runs(data.group_id) })
      }
      if (data.run_id) {
        queryClient.invalidateQueries({ queryKey: ['runs', 'detail', data.run_id] })
      }
    } else if (message.type === 'member_joined') {
      // Invalidate groups query to show newly joined group
      queryClient.invalidateQueries({ queryKey: groupKeys.list() })
      logger.debug('Member joined group, refreshing groups list')
    }
  }, [queryClient])

  // Use centralized WebSocket hook with user endpoint
  useWebSocket(`${WS_BASE_URL}/ws/user`, {
    onMessage: handleWebSocketMessage,
  })

  const handleGroupClick = (groupId: string) => {
    onGroupSelect(groupId)
  }

  const handleNewGroupSuccess = (_newGroup: Group) => {
    setShowNewGroupPopup(false)
    // Invalidate groups query to refetch with new group
    queryClient.invalidateQueries({ queryKey: groupKeys.list() })
  }

  const handleNewStoreSuccess = (_newStore: Store) => {
    setShowNewStorePopup(false)
    // Store has been added, no need to update state here
    // It will be available when creating new runs
  }

  const handleNewProductSuccess = () => {
    setShowNewProductPopup(false)
    // Product has been added, no need to update state here
    // It will be available when searching for products
  }

  return (
    <>
      <Suspense fallback={null}>
        {showNewGroupPopup && (
          <NewGroupPopup
            onClose={() => setShowNewGroupPopup(false)}
            onSuccess={handleNewGroupSuccess}
          />
        )}

        {showNewStorePopup && (
          <NewStorePopup
            onClose={() => setShowNewStorePopup(false)}
            onSuccess={handleNewStoreSuccess}
          />
        )}

        {showNewProductPopup && (
          <NewProductPopup
            onClose={() => setShowNewProductPopup(false)}
            onSuccess={handleNewProductSuccess}
          />
        )}
      </Suspense>

      <div className="groups-container">
        {/* Pending reassignment requests banner */}
        {pendingReassignments.sent.length > 0 && (
          <div className="alert alert-info reassignment-pending-banner">
            <strong>{t('groups:reassignment.pendingTitle')}</strong> {t('groups:reassignment.pendingCount', { count: pendingReassignments.sent.length })}
            {pendingReassignments.sent.map(req => (
              <div key={req.id} style={{ marginTop: '0.5rem', fontSize: '0.9em' }}>
                → {req.store_name} ({t('groups:reassignment.waitingFor', { name: req.to_user_name })})
              </div>
            ))}
          </div>
        )}

        <div className="groups-header">
          <h3>{t('groups:title')}</h3>
          <div className="header-buttons">
            <button onClick={() => setShowNewProductPopup(true)} className="btn btn-secondary">
              {t('groups:actions.newProduct')}
            </button>
            <button onClick={() => setShowNewStorePopup(true)} className="btn btn-secondary">
              {t('groups:actions.newStore')}
            </button>
            <button onClick={() => setShowNewGroupPopup(true)} className="btn btn-primary">
              {t('groups:actions.newGroup')}
            </button>
          </div>
        </div>

      {loading && <p>{t('common:states.loading')}</p>}

      {error && (
        <div className="error">
          <p>❌ {t('groups:errors.loadFailed', { error })}</p>
        </div>
      )}

      {!loading && !error && groups.length === 0 && (
        <div className="no-groups">
          <p>{t('groups:empty.noGroups')}</p>
          <p>{t('groups:empty.invite')}</p>
        </div>
      )}

      {!loading && !error && groups.length > 0 && (
        <div className="groups-list">
          {groups.map((group) => (
            <GroupItem
              key={group.id}
              group={group}
              onGroupClick={handleGroupClick}
              onRunSelect={onRunSelect}
            />
          ))}
        </div>
      )}
    </div>
    </>
  )
}