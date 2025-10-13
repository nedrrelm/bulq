import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import '../styles/components/ManageGroupPage.css'
import { groupsApi, ApiError } from '../api'
import type { GroupManageDetails, GroupMember } from '../api'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAuth } from '../contexts/AuthContext'
import { WS_BASE_URL } from '../config'
import Toast from './Toast'
import ConfirmDialog from './ConfirmDialog'
import { NAVIGATION_DELAY_AFTER_ACTION_MS } from '../constants'

export default function ManageGroupPage() {
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
        setError(err instanceof ApiError ? err.message : 'Failed to load group members')
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
        const action = message.type === 'member_removed' ? 'removed from' : 'left'
        showToast(`You have ${action} this group`, 'error')
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
          showToast(`${message.data.user_name} left the group`, 'info')
        }
      }
    } else if (message.type === 'member_joined') {
      // Add new member to the list
      if (group) {
        const newMember: GroupMember = {
          id: message.data.user_id,
          name: message.data.user_name,
          email: message.data.user_email,
          is_group_admin: false
        }
        setGroup({
          ...group,
          members: [...group.members, newMember]
        })
        showToast(`${message.data.user_name} joined the group`, 'success')
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
        showToast(`${message.data.promoted_user_name} promoted to admin`, 'success')
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
        showToast('Invite link copied to clipboard!', 'success')
      })
      .catch(err => {
        console.error('Failed to copy:', err)
        showToast('Failed to copy invite link', 'error')
      })
  }

  const handleRegenerateToken = async () => {
    if (!group || !group.is_current_user_admin) return

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

  const handleToggleJoining = async () => {
    if (!group || !group.is_current_user_admin) return

    try {
      const data = await groupsApi.toggleJoiningAllowed(groupId)
      setGroup({ ...group, is_joining_allowed: data.is_joining_allowed })
      showToast(
        data.is_joining_allowed ? 'Joining enabled' : 'Joining disabled',
        'success'
      )
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'Failed to update joining setting', 'error')
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
        showToast(`${member.name} removed from group`, 'success')
      } catch (err) {
        showToast(err instanceof ApiError ? err.message : 'Failed to remove member', 'error')
      }
    }

    showConfirm(
      `Are you sure you want to remove ${member.name} from the group?`,
      removeAction,
      { danger: true }
    )
  }

  const handleLeaveGroup = () => {
    if (!group) return

    const leaveAction = async () => {
      try {
        await groupsApi.leaveGroup(groupId)
        showToast('You have left the group', 'success')
        setTimeout(() => {
          navigate(`/groups/${groupId}`)
        }, NAVIGATION_DELAY_AFTER_ACTION_MS)
      } catch (err) {
        showToast(err instanceof ApiError ? err.message : 'Failed to leave group', 'error')
      }
    }

    showConfirm(
      'Are you sure you want to leave this group?',
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
        showToast(`${member.name} promoted to admin`, 'success')
      } catch (err) {
        showToast(err instanceof ApiError ? err.message : 'Failed to promote member', 'error')
      }
    }

    showConfirm(
      `Promote ${member.name} to admin?`,
      promoteAction
    )
  }

  if (loading) {
    return (
      <div className="manage-group-page">
        <p>Loading group members...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="manage-group-page">
        <div className="error">
          <p>❌ {error}</p>
          <button onClick={onBack} className="btn btn-secondary">
            Back
          </button>
        </div>
      </div>
    )
  }

  if (!group) {
    return (
      <div className="manage-group-page">
        <p>Group not found</p>
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
        <span>Manage</span>
      </div>

      <h2>Manage Group</h2>

      {/* Invite Link Section */}
      <section className="manage-section">
        <h3>Invite Link</h3>
        <div className="invite-controls">
          <button onClick={handleCopyInviteLink} className="btn btn-secondary">
            📋 Copy Invite Link
          </button>
          {group.is_current_user_admin && (
            <>
              <button onClick={handleRegenerateToken} className="btn btn-secondary">
                🔄 Regenerate Link
              </button>
              <button
                onClick={handleToggleJoining}
                className={`btn ${group.is_joining_allowed ? 'btn-danger' : 'btn-success'}`}
              >
                {group.is_joining_allowed ? '🔒 Disallow Joining' : '🔓 Allow Joining'}
              </button>
            </>
          )}
        </div>
        {!group.is_joining_allowed && (
          <div className="alert alert-warning">
            ⚠️ Joining is currently disabled. New members cannot join via invite link.
          </div>
        )}
      </section>

      {/* Members Section */}
      <section className="manage-section">
        <h3>Members ({group.members.length})</h3>
        <div className="members-list">
          {group.members.map((member) => (
            <div key={member.id} className="member-item">
              <div className="member-info">
                <div className="member-name">
                  {member.name}
                  {member.is_group_admin && (
                    <span className="admin-badge">Admin</span>
                  )}
                </div>
                <div className="member-email">{member.email}</div>
              </div>
              {group.is_current_user_admin && !member.is_group_admin && (
                <div className="member-actions">
                  <button
                    onClick={() => handlePromoteMember(member)}
                    className="btn btn-secondary btn-small"
                    title="Promote to admin"
                  >
                    ⬆
                  </button>
                  <button
                    onClick={() => handleRemoveMember(member)}
                    className="btn btn-danger btn-small"
                    title="Remove member"
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
        <h3>Leave Group</h3>
        <button onClick={handleLeaveGroup} className="btn btn-danger">
          🚪 Leave Group
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
