import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import '../styles/components/JoinGroup.css'
import { groupsApi } from '../api'
import { API_BASE_URL } from '../config'
import { getErrorMessage } from '../utils/errorHandling'

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
  const [groupPreview, setGroupPreview] = useState<GroupInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [joining, setJoining] = useState(false)
  const [joinedGroup, setJoinedGroup] = useState<GroupInfo | null>(null)

  useEffect(() => {
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
  }, [inviteToken])

  const handleJoin = async () => {
    try {
      setJoining(true)
      setError('')

      const data = await groupsApi.joinGroup(inviteToken)
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
    } catch (err) {
      setError(getErrorMessage(err, t('group:join.errors.joinFailed')))
      setJoining(false)
    }
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
            disabled={joining || !groupPreview}
          >
            {joining ? t('group:join.actions.joining') : t('group:join.actions.submit')}
          </button>
        </div>
      </div>
    </div>
  )
}
