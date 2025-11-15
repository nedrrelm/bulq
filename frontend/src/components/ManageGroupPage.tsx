import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import '../styles/components/ManageGroupPage.css'
import { groupsApi } from '../api'
import type { GroupManageDetails, GroupMember } from '../schemas/group'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAuth } from '../contexts/AuthContext'
import { WS_BASE_URL } from '../config'
import Toast from './Toast'
import ConfirmDialog from './ConfirmDialog'
import { NAVIGATION_DELAY_AFTER_ACTION_MS } from '../constants'
import { getErrorMessage } from '../utils/errorHandling'
import { logger } from '../utils/logger'

export default function ManageGroupPage() {
  const { t } = useTranslation(['group'])
  const { groupId } = useParams<{ groupId: string }>()
  const navigate = useNavigate()

  // Redirect if no groupId
  if (!groupId) {
    navigate('/')
    return null
  }
  const [group, setGroup] = useState<GroupManageDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const { toast, showToast, hideToast } = useToast()
  const { confirmState, showConfirm, hideConfirm, handleConfirm } = useConfirm()
  const { user } = useAuth()

  useEffect(() => {
    const fetchGroupMembers = async () => {
      try {
        setLoading(true)
        setError('')
        const data = await groupsApi.getGroupMembers(groupId)
        setGroup(data)
      } catch (err) {
        setError(getErrorMessage(err, t('group:manage.errors.loadFailed')))
      } finally {
        setLoading(false)
      }
    }

    fetchGroupMembers()
  }, [groupId])

  // WebSocket handler for real-time updates
  const handleWebSocketMessage = useCallback((message: any) => {
    if (message.type === 'member_removed' || message.type === 'member_left') {
      // Use the appropriate user_id field based on message type
      const userId = message.type === 'member_removed'
        ? message.data.removed_user_id
        : message.data.user_id

      // If current user was removed or left, redirect to main page
      if (user && userId === user.id) {
        const messageKey = message.type === 'member_removed'
          ? 'group.manage.messages.youWereRemoved'
          : 'group.manage.messages.youLeft'
        showToast(t(messageKey), 'error')
        setTimeout(() => {
          navigate(`/groups/${groupId}`)
        }, NAVIGATION_DELAY_AFTER_ACTION_MS)
        return
      }

      // Otherwise, just update the member list
      if (group) {
        setGroup({
          ...group,
          members: group.members.filter(m => m.id !== userId)
        })

        // Show toast for other members leaving
        if (message.type === 'member_left') {
          showToast(t('group:manage.messages.memberLeft', { memberName: message.data.user_name }), 'info')
        }
      }
    } else if (message.type === 'member_joined') {
      // Add new member to the list
      if (group) {
        const newMember: GroupMember = {
          id: message.data.user_id,
          name: message.data.user_name,
          username: message.data.user_username,
          is_group_admin: false
        }
        setGroup({
          ...group,
          members: [...group.members, newMember]
        })
        showToast(t('group:manage.messages.memberJoined', { memberName: message.data.user_name }), 'success')
      }
    } else if (message.type === 'member_promoted') {
      // Update member admin status
      if (group) {
        setGroup({
          ...group,
          members: group.members.map(m =>
            m.id === message.data.promoted_user_id ? { ...m, is_group_admin: true } : m
          )
        })
        showToast(t('group:manage.messages.memberPromoted', { memberName: message.data.promoted_user_name }), 'success')
      }
    }
  }, [group, user, showToast])

  useWebSocket(
    groupId ? `${WS_BASE_URL}/ws/groups/${groupId}` : null,
    {
      onMessage: handleWebSocketMessage
    }
  )

  const onBack = () => {
    navigate(`/groups/${groupId}`)
  }

  const handleCopyInviteLink = () => {
    if (!group) return
    const inviteUrl = `${window.location.origin}/invite/${group.invite_token}`
    navigator.clipboard.writeText(inviteUrl)
      .then(() => {
        showToast(t('group:manage.messages.inviteCopied'), 'success')
      })
      .catch(err => {
        logger.error('Failed to copy:', err)
        showToast(t('group:manage.errors.copyFailed'), 'error')
      })
  }

  const handleRegenerateToken = async () => {
    if (!group || !group.is_current_user_admin) return

    const regenerateAction = async () => {
      try {
        const data = await groupsApi.regenerateInvite(groupId)
        setGroup({ ...group, invite_token: data.invite_token })
        showToast(t('group:manage.messages.inviteRegenerated'), 'success')
      } catch (err) {
        showToast(getErrorMessage(err, t('group:manage.errors.regenerateFailed')), 'error')
      }
    }

    showConfirm(
      t('group:manage.confirm.regenerateInvite'),
      regenerateAction,
      { danger: true }
    )
  }

  const handleToggleJoining = async () => {
    if (!group || !group.is_current_user_admin) return

    try {
      const data = await groupsApi.toggleJoiningAllowed(groupId)
      setGroup({ ...group, is_joining_allowed: data.is_joining_allowed })
      showToast(
        t(data.is_joining_allowed ? 'group.manage.messages.joiningEnabled' : 'group.manage.messages.joiningDisabled'),
        'success'
      )
    } catch (err) {
      showToast(getErrorMessage(err, t('group:manage.errors.toggleJoiningFailed')), 'error')
    }
  }

  const handleRemoveMember = (member: GroupMember) => {
    if (!group || !group.is_current_user_admin) return

    const removeAction = async () => {
      try {
        await groupsApi.removeMember(groupId, member.id)
        setGroup({
          ...group,
          members: group.members.filter(m => m.id !== member.id)
        })
        showToast(t('group:manage.messages.memberRemoved', { memberName: member.name }), 'success')
      } catch (err) {
        showToast(getErrorMessage(err, t('group:manage.errors.removeFailed')), 'error')
      }
    }

    showConfirm(
      t('group:manage.confirm.removeMember', { memberName: member.name }),
      removeAction,
      { danger: true }
    )
  }

  const handleLeaveGroup = () => {
    if (!group) return

    const leaveAction = async () => {
      try {
        await groupsApi.leaveGroup(groupId)
        showToast(t('group:manage.messages.leftGroup'), 'success')
        setTimeout(() => {
          navigate(`/groups/${groupId}`)
        }, NAVIGATION_DELAY_AFTER_ACTION_MS)
      } catch (err) {
        showToast(getErrorMessage(err, t('group:manage.errors.leaveFailed')), 'error')
      }
    }

    showConfirm(
      t('group:manage.confirm.leaveGroup'),
      leaveAction,
      { danger: true }
    )
  }

  const handlePromoteMember = (member: GroupMember) => {
    if (!group || !group.is_current_user_admin) return

    const promoteAction = async () => {
      try {
        await groupsApi.promoteMemberToAdmin(groupId, member.id)
        // Update local state to reflect the promotion
        setGroup({
          ...group,
          members: group.members.map(m =>
            m.id === member.id ? { ...m, is_group_admin: true } : m
          )
        })
        showToast(t('group:manage.messages.memberPromoted', { memberName: member.name }), 'success')
      } catch (err) {
        showToast(getErrorMessage(err, t('group:manage.errors.promoteFailed')), 'error')
      }
    }

    showConfirm(
      t('group:manage.confirm.promoteMember', { memberName: member.name }),
      promoteAction
    )
  }

  if (loading) {
    return (
      <div className="manage-group-page">
        <p>{t('group:manage.loading')}</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="manage-group-page">
        <div className="error">
          <p>{error}</p>
          <button onClick={onBack} className="btn btn-secondary">
            {t('group:manage.actions.back')}
          </button>
        </div>
      </div>
    )
  }

  if (!group) {
    return (
      <div className="manage-group-page">
        <p>{t('group:manage.errors.notFound')}</p>
      </div>
    )
  }

  return (
    <div className="manage-group-page">
      <div className="breadcrumb">
        <span className="breadcrumb-link" onClick={onBack}>
          {group.name}
        </span>
        <span className="breadcrumb-separator"> / </span>
        <span>{t('group:manage.breadcrumb')}</span>
      </div>

      <h2>{t('group:manage.title')}</h2>

      {/* Invite Link Section */}
      <section className="manage-section">
        <h3>{t('group:manage.sections.inviteLink')}</h3>
        <div className="invite-controls">
          <button onClick={handleCopyInviteLink} className="btn btn-secondary">
            {t('group:manage.actions.copyInvite')}
          </button>
          {group.is_current_user_admin && (
            <>
              <button onClick={handleRegenerateToken} className="btn btn-secondary">
                {t('group:manage.actions.regenerateInvite')}
              </button>
              <button
                onClick={handleToggleJoining}
                className={`btn ${group.is_joining_allowed ? 'btn-danger' : 'btn-success'}`}
              >
                {t(group.is_joining_allowed ? 'group.manage.actions.disallowJoining' : 'group.manage.actions.allowJoining')}
              </button>
            </>
          )}
        </div>
        {!group.is_joining_allowed && (
          <div className="alert alert-warning">
            {t('group:manage.warnings.joiningDisabled')}
          </div>
        )}
      </section>

      {/* Members Section */}
      <section className="manage-section">
        <h3>{t('group:manage.sections.members')} ({group.members.length})</h3>
        <div className="members-list">
          {group.members.map((member) => (
            <div key={member.id} className="member-item">
              <div className="member-info">
                <div className="member-name">
                  {member.name}
                  {member.is_group_admin && (
                    <span className="admin-badge">{t('group:manage.labels.admin')}</span>
                  )}
                </div>
                <div className="member-email">@{member.username}</div>
              </div>
              {group.is_current_user_admin && !member.is_group_admin && (
                <div className="member-actions">
                  <button
                    onClick={() => handlePromoteMember(member)}
                    className="btn btn-secondary btn-small"
                    title={t('group:manage.actions.promote')}
                  >
                    ⬆
                  </button>
                  <button
                    onClick={() => handleRemoveMember(member)}
                    className="btn btn-danger btn-small"
                    title={t('group:manage.actions.remove')}
                  >
                    −
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Leave Group Section */}
      <section className="manage-section">
        <h3>{t('group:manage.sections.leaveGroup')}</h3>
        <button onClick={handleLeaveGroup} className="btn btn-danger">
          {t('group:manage.actions.leaveGroup')}
        </button>
      </section>

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
