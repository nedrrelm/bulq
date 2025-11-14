import { useTranslation } from 'react-i18next'
import type { RunDetail } from '../api'

type Participant = RunDetail['participants'][0]

interface RunParticipantsProps {
  participants: Participant[]
  currentUserIsReady: boolean
  onToggleReady: () => void
  isToggling: boolean
  canToggleReady: boolean
}

/**
 * RunParticipants - Displays participant ready status in a run
 *
 * Shows which participants are ready and allows the current user
 * to toggle their ready status when in active state.
 */
export default function RunParticipants({
  participants,
  currentUserIsReady,
  onToggleReady,
  isToggling,
  canToggleReady
}: RunParticipantsProps) {
  const { t } = useTranslation()

  return (
    <div className="participants-section">
      <h3>{t('run.participants.title', { count: participants.length })}</h3>
      <div className="participants-list">
        {participants.map((participant) => (
          <div key={participant.user_id} className="participant-item">
            <div className="participant-info">
              <span className="participant-name">{participant.user_name}</span>
              {participant.is_ready && (
                <span className="ready-badge">✓ {t('run.participants.ready')}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {canToggleReady && (
        <div className="ready-section">
          <label className="ready-checkbox">
            <input
              type="checkbox"
              checked={currentUserIsReady}
              onChange={onToggleReady}
              disabled={isToggling}
            />
            <span>
              {isToggling ? t('run.participants.updating') : t('run.participants.imReady')}
            </span>
          </label>
          <p className="ready-hint">
            {t('run.participants.readyHint')}
          </p>
        </div>
      )}
    </div>
  )
}
