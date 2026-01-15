import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import '../styles/components/JoinGroup.css'
import { API_BASE_URL } from '../config'
import { getErrorMessage } from '../utils/errorHandling'
import { redirectStorage } from '../utils/redirectStorage'
import { useAuth } from '../contexts/AuthContext'
import { useJoinGroup } from '../hooks/queries/useGroups'

interface JoinGroupProps {
  inviteToken: string
  onJoinSuccess: () => void
}

interface GroupInfo {
  id: string
  name: string
  member_count: number
  creator_name: string
}

export default function JoinGroup({ inviteToken, onJoinSuccess }: JoinGroupProps) {
  const { t } = useTranslation(['group'])
  const { user } = useAuth()
  const navigate = useNavigate()
  const joinGroupMutation = useJoinGroup()

  const [groupPreview, setGroupPreview] = useState<GroupInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [joinedGroup, setJoinedGroup] = useState<GroupInfo | null>(null)

  // Check authentication and redirect if necessary
  useEffect(() => {
    if (user === null) {
      // User is not authenticated, store invite token and redirect to login
      redirectStorage.setPendingInvite(inviteToken)
      navigate(`/?inviteToken=${inviteToken}`)
    }
  }, [user, inviteToken, navigate])

  useEffect(() => {
    // Don't fetch if user is not authenticated
    if (!user) return

    const fetchGroupInfo = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${API_BASE_URL}/groups/preview/${inviteToken}`)

        if (!response.ok) {
          throw new Error(t('group:join.errors.invalidInvite'))
        }

        const data: GroupInfo = await response.json()
        setGroupPreview(data)
      } catch (err) {
        setError(getErrorMessage(err, t('group:join.errors.loadFailed')))
      } finally {
        setLoading(false)
      }
    }

    fetchGroupInfo()
  }, [inviteToken, user])

  const handleJoin = () => {
    setError('')

    joinGroupMutation.mutate(inviteToken, {
      onSuccess: (data) => {
        setJoinedGroup({
          id: data.group_id,
          name: data.group_name,
          member_count: groupPreview?.member_count || 0,
          creator_name: groupPreview?.creator_name || ''
        })

        // Show success message briefly then redirect
        setTimeout(() => {
          onJoinSuccess()
        }, 1500)
      },
      onError: (err) => {
        setError(getErrorMessage(err, t('group:join.errors.joinFailed')))
      }
    })
  }

  if (loading) {
    return (
      <div className="join-group-page">
        <div className="join-group-card">
          <p>{t('group:join.loading')}</p>
        </div>
      </div>
    )
  }

  if (joinedGroup) {
    return (
      <div className="join-group-page">
        <div className="join-group-card">
          <div className="success-icon">✅</div>
          <h2>{t('group:join.success.title')}</h2>
          <p>{t('group:join.success.message', { groupName: joinedGroup.name })}</p>
          <p className="redirect-message">{t('group:join.success.redirecting')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="join-group-page">
      <div className="join-group-card">
        <h2>{t('group:join.title')}</h2>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {groupPreview && (
          <div className="group-preview">
            <h3>{groupPreview.name}</h3>
            <div className="group-details">
              <p><strong>{t('group:join.preview.createdBy')}:</strong> {groupPreview.creator_name}</p>
              <p><strong>{t('group:join.preview.members')}:</strong> {groupPreview.member_count}</p>
            </div>
            <p className="invite-message">{t('group:join.preview.inviteMessage')}</p>
          </div>
        )}

        <div className="join-actions">
          <button
            onClick={handleJoin}
            className="btn btn-primary"
            disabled={joinGroupMutation.isPending || !groupPreview}
          >
            {joinGroupMutation.isPending ? t('group:join.actions.joining') : t('group:join.actions.submit')}
          </button>
        </div>
      </div>
    </div>
  )
}
