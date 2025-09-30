import { useState, useEffect } from 'react'
import './Groups.css'

interface Group {
  id: string
  name: string
  description: string
  member_count: number
  created_at: string
}

interface GroupsProps {
  onGroupSelect: (groupId: string) => void
}

export default function Groups({ onGroupSelect }: GroupsProps) {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const BACKEND_URL = 'http://localhost:8000'

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        setLoading(true)
        setError('')

        const response = await fetch(`${BACKEND_URL}/groups/my-groups`, {
          credentials: 'include'
        })

        if (!response.ok) {
          const errorText = await response.text()
          throw new Error(`HTTP error! status: ${response.status} - ${errorText}`)
        }

        const groupsData: Group[] = await response.json()
        setGroups(groupsData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load groups')
      } finally {
        setLoading(false)
      }
    }

    fetchGroups()
  }, [])

  const handleGroupClick = (groupId: string) => {
    onGroupSelect(groupId)
  }

  return (
    <div className="groups-panel">
      <h3>My Groups</h3>

      {loading && <p>Loading groups...</p>}

      {error && (
        <div className="error">
          <p>❌ Failed to load groups: {error}</p>
        </div>
      )}

      {!loading && !error && groups.length === 0 && (
        <div className="no-groups">
          <p>You haven't joined any groups yet.</p>
          <p>Ask a friend to invite you to their group!</p>
        </div>
      )}

      {!loading && !error && groups.length > 0 && (
        <div className="groups-list">
          {groups.map((group) => (
            <div
              key={group.id}
              className="group-item"
              onClick={() => handleGroupClick(group.id)}
            >
              <div className="group-header">
                <h4>{group.name}</h4>
                <span className="member-count">{group.member_count} members</span>
              </div>
              <p className="group-description">{group.description}</p>
              <p className="group-date">
                Joined: {new Date(group.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}