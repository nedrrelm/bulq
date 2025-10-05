import { useState, useEffect } from 'react'
import './JoinGroup.css'

interface JoinGroupProps {
  inviteToken: string
  onJoinSuccess: () => void
}

interface GroupInfo {
  id: string
  name: string
}

export default function JoinGroup({ inviteToken, onJoinSuccess }: JoinGroupProps) {
  const [groupInfo, setGroupInfo] = useState<GroupInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [joining, setJoining] = useState(false)

  const BACKEND_URL = 'http://localhost:8000'

  useEffect(() => {
    const fetchGroupInfo = async () => {
      try {
        setLoading(true)
        setError('')

        // We need to get group info first - we'll try to join and see the response
        // Or we can add a new endpoint to just preview the group
        // For now, let's just show the token and allow joining
        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load group info')
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
      setGroupInfo({ id: data.group_id, name: data.group_name })

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

  if (groupInfo) {
    return (
      <div className="join-group-page">
        <div className="join-group-card">
          <div className="success-icon">✅</div>
          <h2>Successfully Joined!</h2>
          <p>You've joined the group: <strong>{groupInfo.name}</strong></p>
          <p className="redirect-message">Redirecting to your groups...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="join-group-page">
      <div className="join-group-card">
        <h2>Join Group</h2>
        <p>You've been invited to join a group on Bulq!</p>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <div className="join-actions">
          <button
            onClick={handleJoin}
            className="btn btn-primary"
            disabled={joining}
          >
            {joining ? 'Joining...' : 'Join Group'}
          </button>
        </div>
      </div>
    </div>
  )
}
