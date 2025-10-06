import { useState, useEffect } from 'react'
import './Groups.css'
import NewGroupPopup from './NewGroupPopup'

interface RunSummary {
  id: string
  store_name: string
  state: string
}

interface Group {
  id: string
  name: string
  description: string
  member_count: number
  active_runs_count: number
  completed_runs_count: number
  active_runs: RunSummary[]
  created_at: string
}

interface GroupsProps {
  onGroupSelect: (groupId: string) => void
  onRunSelect: (runId: string) => void
  onProductSelect: (productId: string) => void
}

interface ProductSearchResult {
  id: string
  name: string
  store_id: string
  store_name: string
  base_price: number | null
}

export default function Groups({ onGroupSelect, onRunSelect, onProductSelect }: GroupsProps) {
  const [groups, setGroups] = useState<Group[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showNewGroupPopup, setShowNewGroupPopup] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<ProductSearchResult[]>([])
  const [searching, setSearching] = useState(false)

  const BACKEND_URL = 'http://localhost:8000'

  const getStateLabel = (state: string) => {
    switch (state) {
      case 'planning':
        return 'Planning'
      case 'active':
        return 'Active'
      case 'confirmed':
        return 'Confirmed'
      case 'shopping':
        return 'Shopping'
      case 'adjusting':
        return 'Adjusting'
      case 'distributing':
        return 'Distributing'
      case 'completed':
        return 'Completed'
      case 'cancelled':
        return 'Cancelled'
      default:
        return state
    }
  }

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

  const handleNewGroupSuccess = () => {
    setShowNewGroupPopup(false)
    // Refresh the groups list
    const fetchGroups = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/groups/my-groups`, {
          credentials: 'include'
        })
        if (response.ok) {
          const groupsData: Group[] = await response.json()
          setGroups(groupsData)
        }
      } catch (err) {
        console.error('Failed to refresh groups:', err)
      }
    }
    fetchGroups()
  }

  const handleSearch = async (query: string) => {
    setSearchQuery(query)

    if (query.trim().length < 2) {
      setSearchResults([])
      return
    }

    try {
      setSearching(true)
      const response = await fetch(`${BACKEND_URL}/products/search?q=${encodeURIComponent(query)}`, {
        credentials: 'include'
      })

      if (response.ok) {
        const results: ProductSearchResult[] = await response.json()
        setSearchResults(results)
      } else {
        setSearchResults([])
      }
    } catch (err) {
      console.error('Search failed:', err)
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  return (
    <>
      {showNewGroupPopup && (
        <NewGroupPopup
          onClose={() => setShowNewGroupPopup(false)}
          onSuccess={handleNewGroupSuccess}
        />
      )}

      <div className="product-search-panel card">
        <h3>Search Products</h3>
        <div className="search-box">
          <input
            type="text"
            placeholder="Search for products..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="form-input"
          />
        </div>

        {searching && <p className="search-status">Searching...</p>}

        {searchResults.length > 0 && (
          <div className="search-results">
            {searchResults.map((product) => (
              <div
                key={product.id}
                className="product-result"
                onClick={() => onProductSelect(product.id)}
              >
                <div className="product-info">
                  <strong>{product.name}</strong>
                  <span className="product-store">{product.store_name}</span>
                </div>
                {product.base_price && (
                  <span className="product-price">${product.base_price.toFixed(2)}</span>
                )}
              </div>
            ))}
          </div>
        )}

        {searchQuery.trim().length >= 2 && !searching && searchResults.length === 0 && (
          <p className="search-status">No products found</p>
        )}
      </div>

      <div className="groups-panel">
        <div className="groups-header">
          <h3>My Groups</h3>
          <button onClick={() => setShowNewGroupPopup(true)} className="btn btn-primary">
            + New Group
          </button>
        </div>

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
              </div>
              <div className="group-stats">
                <span className="stat">
                  <span className="stat-icon">👥</span>
                  {group.member_count} {group.member_count === 1 ? 'member' : 'members'}
                </span>
                <span className="stat">
                  <span className="stat-icon">✅</span>
                  {group.completed_runs_count} completed {group.completed_runs_count === 1 ? 'run' : 'runs'}
                </span>
              </div>

              {group.active_runs.length > 0 && (
                <div className="active-runs">
                  {group.active_runs.map((run) => (
                    <div
                      key={run.id}
                      className="run-summary"
                      onClick={(e) => {
                        e.stopPropagation()
                        onRunSelect(run.id)
                      }}
                    >
                      <span className="run-store">{run.store_name}</span>
                      <span className={`run-state state-${run.state}`}>{getStateLabel(run.state)}</span>
                    </div>
                  ))}
                  {group.active_runs_count > 3 && (
                    <div className="more-runs">
                      +{group.active_runs_count - 3} more...
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      </div>
    </>
  )
}