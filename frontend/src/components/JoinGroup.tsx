import { useState, useEffect } from 'react'
import './JoinGroup.css'

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
  const [groupPreview, setGroupPreview] = useState<GroupInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [joining, setJoining] = useState(false)
  const [joinedGroup, setJoinedGroup] = useState<GroupInfo | null>(null)

  const BACKEND_URL = 'http://localhost:8000'

  useEffect(() => {
    const fetchGroupInfo = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${BACKEND_URL}/groups/preview/${inviteToken}`)

        if (!response.ok) {
          throw new Error('Invalid or expired invite link')
        }

        const data: GroupInfo = await response.json()
        setGroupPreview(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load group info')
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

      const response = await fetch(`${BACKEND_URL}/groups/join/${inviteToken}`, {
        method: 'POST',
        credentials: 'include'
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to join group')
      }

      const data = await response.json()
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
      setError(err instanceof Error ? err.message : 'Failed to join group')
      setJoining(false)
    }
  }

  if (loading) {
    return (
      <div className="join-group-page">
        <div className="join-group-card">
          <p>Loading group information...</p>
        </div>
      </div>
    )
  }

  if (joinedGroup) {
    return (
      <div className="join-group-page">
        <div className="join-group-card">
          <div className="success-icon">✅</div>
          <h2>Successfully Joined!</h2>
          <p>You've joined the group: <strong>{joinedGroup.name}</strong></p>
          <p className="redirect-message">Redirecting to your groups...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="join-group-page">
      <div className="join-group-card">
        <h2>Join Group</h2>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {groupPreview && (
          <div className="group-preview">
            <h3>{groupPreview.name}</h3>
            <div className="group-details">
              <p><strong>Created by:</strong> {groupPreview.creator_name}</p>
              <p><strong>Members:</strong> {groupPreview.member_count}</p>
            </div>
            <p className="invite-message">You've been invited to join this group!</p>
          </div>
        )}

        <div className="join-actions">
          <button
            onClick={handleJoin}
            className="btn btn-primary"
            disabled={joining || !groupPreview}
          >
            {joining ? 'Joining...' : 'Join Group'}
          </button>
        </div>
      </div>
    </div>
  )
}
