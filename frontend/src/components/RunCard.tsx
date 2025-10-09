import { Link } from 'react-router-dom'
import '../styles/components/RunCard.css'
import '../styles/run-states.css'
import { getStateLabel } from '../utils/runStates'

interface Run {
  id: string
  store_name: string
  state: string
  leader_name: string
  leader_is_removed?: boolean
  planned_on: string | null
  group_name?: string
}

interface RunCardProps {
  run: Run
  onClick?: (runId: string) => void
  showAsLink?: boolean
  showGroupName?: boolean
}

function RunCard({ run, onClick, showAsLink = true, showGroupName = false }: RunCardProps) {
  const content = (
    <div className="run-card-content">
      <div className="run-card-header">
        <h4>{run.store_name}</h4>
        <span className={`run-state state-${run.state}`}>
          {getStateLabel(run.state)}
        </span>
      </div>
      <div className="run-card-details">
        {showGroupName && run.group_name && (
          <div className="run-detail">
            <span className="run-detail-label">Group:</span>
            <span className="run-detail-value">{run.group_name}</span>
          </div>
        )}
        <div className="run-detail">
          <span className="run-detail-label">Leader:</span>
          <span className={`run-detail-value ${run.leader_is_removed ? 'removed-user' : ''}`}>
            {run.leader_name}
          </span>
        </div>
        {run.planned_on && (
          <div className="run-detail">
            <span className="run-detail-label">Planned:</span>
            <span className="run-detail-value">
              {new Date(run.planned_on).toLocaleDateString()}
            </span>
          </div>
        )}
      </div>
    </div>
  )

  if (showAsLink) {
    return (
      <Link to={`/runs/${run.id}`} className="run-card card">
        {content}
      </Link>
    )
  }

  return (
    <div
      className="run-card card clickable"
      onClick={() => onClick && onClick(run.id)}
    >
      {content}
    </div>
  )
}

export default RunCard
