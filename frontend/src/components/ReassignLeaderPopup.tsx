import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { reassignmentApi } from '../api'
import '../styles/components/ReassignLeaderPopup.css'
import { getErrorMessage } from '../utils/errorHandling'

interface Participant {
  user_id: string
  user_name: string
  is_leader: boolean
}

interface ReassignLeaderPopupProps {
  runId: string
  participants: Participant[]
  onClose: () => void
  onSuccess: () => void
  onCancelRun?: () => void
}

export default function ReassignLeaderPopup({
  runId,
  participants,
  onClose,
  onSuccess,
  onCancelRun,
}: ReassignLeaderPopupProps) {
  const { t } = useTranslation(['common', 'run'])
  const [selectedUserId, setSelectedUserId] = useState<string>('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string>('')

  // Filter out the current leader
  const eligibleParticipants = participants.filter(p => !p.is_leader)

  // Handle ESC key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !submitting) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose, submitting])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedUserId) {
      setError(t('run:validation.participantRequired'))
      return
    }

    try {
      setSubmitting(true)
      setError('')
      await reassignmentApi.requestReassignment(runId, selectedUserId)
      onSuccess()
      onClose()
    } catch (err: any) {
      setError(getErrorMessage(err, t('run:errors.reassignmentFailed')))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-md" onClick={(e) => e.stopPropagation()}>
        <h2>{t('run:reassign.title')}</h2>
        <p className="text-sm" style={{ color: 'var(--color-text-light)', marginBottom: '1.5rem' }}>
          {t('run:reassign.description')}
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="participant" className="form-label">
              {t('run:fields.newLeader')}
            </label>
            <select
              id="participant"
              className="form-input"
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              disabled={submitting}
              required
            >
              <option value="">{t('run:reassign.selectParticipant')}</option>
              {eligibleParticipants.map((participant) => (
                <option key={participant.user_id} value={participant.user_id}>
                  {participant.user_name}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
              {error}
            </div>
          )}

          {eligibleParticipants.length === 0 && (
            <div className="alert alert-info" style={{ marginBottom: '1rem' }}>
              {t('run:reassign.noParticipantsAvailable')}
            </div>
          )}

          <div className="modal-actions">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={submitting}
            >
              {t('common:buttons.cancel')}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || eligibleParticipants.length === 0}
            >
              {submitting ? t('run:actions.reassigning') : t('run:actions.reassign')}
            </button>
            {onCancelRun && (
              <button
                type="button"
                onClick={() => {
                  onClose()
                  onCancelRun()
                }}
                className="btn btn-danger"
              >
                {t('run:actions.cancelRun')}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}
