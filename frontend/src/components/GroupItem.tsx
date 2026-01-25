import { memo } from 'react'
import { useTranslation } from 'react-i18next'
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
      planned_on?: string | null
      planning_at?: string | null
      active_at?: string | null
      confirmed_at?: string | null
    }>
  }
  onGroupClick: (groupId: string) => void
  onRunSelect: (runId: string) => void
}

const GroupItem = memo(function GroupItem({ group, onGroupClick, onRunSelect }: GroupItemProps) {
  const { t } = useTranslation(['group'])

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
            {group.member_count} {t('group:card.members', { count: group.member_count })}
          </span>
          <span className="stat">
            <span className="stat-icon">✅</span>
            {group.completed_runs_count} {t('group:card.completedRuns', { count: group.completed_runs_count })}
          </span>
        </div>

        {group.active_runs.length > 0 && (
          <div className="active-runs">
            {group.active_runs.map((run) => {
              // Get display date based on state
              const displayDate = run.state === 'planning'
                ? (run.planned_on || run.planning_at)
                : run.state === 'active'
                ? (run.planned_on || run.active_at)
                : run.state === 'confirmed'
                ? (run.planned_on || run.confirmed_at)
                : run.planned_on

              return (
                <div
                  key={run.id}
                  className="run-summary"
                  onClick={(e) => {
                    e.stopPropagation()
                    onRunSelect(run.id)
                  }}
                >
                  <div>
                    <span className="run-store">{run.store_name}</span>
                    {displayDate && (
                      <span className="run-date" style={{ fontSize: '0.85em', marginLeft: '0.5rem', opacity: 0.7 }}>
                        {new Date(displayDate).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  <span className={`run-state state-${run.state}`}>{getStateLabel(run.state)}</span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
})

export default GroupItem
