import { useState, useEffect } from 'react'
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
      setError('Please select a participant')
      return
    }

    try {
      setSubmitting(true)
      setError('')
      await reassignmentApi.requestReassignment(runId, selectedUserId)
      onSuccess()
      onClose()
    } catch (err: any) {
      setError(getErrorMessage(err, 'Failed to request reassignment'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-md" onClick={(e) => e.stopPropagation()}>
        <h2>Reassign Leadership</h2>
        <p className="text-sm" style={{ color: 'var(--color-text-light)', marginBottom: '1.5rem' }}>
          Select a participant to transfer leadership to. They will receive a notification and must accept the request.
        </p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="participant" className="form-label">
              New Leader
            </label>
            <select
              id="participant"
              className="form-input"
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              disabled={submitting}
              required
            >
              <option value="">Select a participant...</option>
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
              No other participants available to reassign to
            </div>
          )}

          <div className="modal-actions">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || eligibleParticipants.length === 0}
            >
              {submitting ? 'Reassigning...' : 'Reassign'}
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
                ✕ Cancel Run
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}
