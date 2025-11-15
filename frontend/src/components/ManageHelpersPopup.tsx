import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useQueryClient } from '@tanstack/react-query'
import { runsApi, groupsApi } from '../api'
import { runKeys } from '../hooks/queries'
import type { RunDetail } from '../api'
import '../styles/components/ManageHelpersPopup.css'
import { formatErrorForDisplay } from '../utils/errorHandling'

interface ManageHelpersPopupProps {
  run: RunDetail
  onClose: () => void
}

interface GroupMember {
  id: string
  name: string
  username: string
  is_group_admin: boolean
}

export default function ManageHelpersPopup({ run, onClose }: ManageHelpersPopupProps) {
  const { t } = useTranslation(['common', 'run'])
  const [loadingUserId, setLoadingUserId] = useState<string | null>(null)
  const [error, setError] = useState<string>('')
  const [groupMembers, setGroupMembers] = useState<GroupMember[]>([])
  const [loadingMembers, setLoadingMembers] = useState(true)
  const queryClient = useQueryClient()

  // Fetch all group members
  useEffect(() => {
    const fetchGroupMembers = async () => {
      try {
        setLoadingMembers(true)
        const response = await groupsApi.getGroupMembers(run.group_id)
        setGroupMembers(response.members || [])
      } catch (err) {
        setError(formatErrorForDisplay(err, 'fetch group members'))
      } finally {
        setLoadingMembers(false)
      }
    }

    fetchGroupMembers()
  }, [run.group_id])

  // Find current leader
  const currentLeader = run.participants.find(p => p.is_leader)

  // Get all eligible members (everyone except the leader)
  const eligibleMembers = groupMembers.filter(
    member => member.id !== currentLeader?.user_id
  )

  // Check if a member is currently a helper
  const isHelper = (userId: string) => {
    const participant = run.participants.find(p => p.user_id === userId)
    return participant?.is_helper || false
  }

  // Handle ESC key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !loadingUserId) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose, loadingUserId])

  const handleToggleHelper = async (userId: string, isCurrentlyHelper: boolean) => {
    try {
      setLoadingUserId(userId)
      setError('')
      await runsApi.toggleHelper(run.id, userId)
      // Invalidate and refetch run details
      queryClient.invalidateQueries({ queryKey: runKeys.detail(run.id) })
    } catch (err) {
      setError(formatErrorForDisplay(err, isCurrentlyHelper ? 'remove helper' : 'add helper'))
    } finally {
      setLoadingUserId(null)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-md" onClick={(e) => e.stopPropagation()}>
        <h2>{t('run:helpers.title')}</h2>
        <p className="text-sm" style={{ color: 'var(--color-text-light)', marginBottom: '1.5rem' }}>
          {t('run:helpers.description')}
        </p>

        {error && (
          <div className="error-message" style={{ marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {loadingMembers ? (
          <p className="text-center" style={{ color: 'var(--color-text-light)', padding: '2rem 0' }}>
            {t('run:helpers.loadingMembers')}
          </p>
        ) : eligibleMembers.length === 0 ? (
          <p className="text-center" style={{ color: 'var(--color-text-light)', padding: '2rem 0' }}>
            {t('run:helpers.noMembersAvailable')}
          </p>
        ) : (
          <div className="helpers-list">
            {eligibleMembers.map(member => {
              const memberIsHelper = isHelper(member.id)
              return (
                <div key={member.id} className="helper-item">
                  <div className="helper-info">
                    <span className="helper-name">{member.name}</span>
                    {memberIsHelper && <span className="helper-badge-small">{t('run:helpers.helperBadge')}</span>}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleToggleHelper(member.id, memberIsHelper)}
                    disabled={loadingUserId === member.id}
                    className={memberIsHelper ? 'btn btn-secondary btn-sm' : 'btn btn-primary btn-sm'}
                  >
                    {loadingUserId === member.id
                      ? '...'
                      : memberIsHelper
                      ? t('run:actions.removeHelper')
                      : t('run:actions.addHelper')}
                  </button>
                </div>
              )
            })}
          </div>
        )}

        <div className="button-group" style={{ marginTop: '1.5rem' }}>
          <button
            type="button"
            onClick={onClose}
            className="btn btn-secondary"
            disabled={!!loadingUserId}
          >
            {t('common:buttons.close')}
          </button>
        </div>
      </div>
    </div>
  )
}
