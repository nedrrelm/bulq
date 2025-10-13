import { memo } from 'react'
import ErrorBoundary from './ErrorBoundary'
import { getStateLabel } from '../utils/runStates'

interface GroupItemProps {
  group: {
    id: string
    name: string
    member_count: number
    completed_runs_count: number
    active_runs: Array<{
      id: string
      store_name: string
      state: string
    }>
  }
  onGroupClick: (groupId: string) => void
  onRunSelect: (runId: string) => void
}

const GroupItem = memo(function GroupItem({ group, onGroupClick, onRunSelect }: GroupItemProps) {
  return (
    <ErrorBoundary>
      <div
        className="group-item"
        onClick={() => onGroupClick(group.id)}
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
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
})

export default GroupItem
