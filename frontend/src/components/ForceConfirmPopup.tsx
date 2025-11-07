import { useState, useRef } from 'react'
import { runsApi, ApiError } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'

interface ForceConfirmPopupProps {
  runId: string
  onClose: () => void
  onSuccess: () => void
}

export default function ForceConfirmPopup({ runId, onClose, onSuccess }: ForceConfirmPopupProps) {
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

  const handleForceConfirm = async (e: React.FormEvent) => {
    e.preventDefault()

    try {
      setSubmitting(true)
      setError('')

      await runsApi.forceConfirm(runId)
      onSuccess()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to force confirm run')
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Force Confirm Run</h2>
        </div>

        <form onSubmit={handleForceConfirm}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ marginBottom: '1rem' }}>
              <strong>Warning:</strong> This will move the run to the confirmed state without waiting for all participants to mark themselves as ready.
            </p>
            <p style={{ marginBottom: '1rem', color: 'var(--color-text-secondary)' }}>
              Use this if:
            </p>
            <ul style={{ marginLeft: '1.5rem', color: 'var(--color-text-secondary)' }}>
              <li>Some participants are not responding</li>
              <li>You need to proceed with the run urgently</li>
              <li>You've confirmed participation outside the app</li>
            </ul>
            <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
              Once confirmed, participants will not be able to change their bids.
            </p>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn"
              style={{ backgroundColor: 'var(--color-warning)', color: 'white' }}
              disabled={submitting}
            >
              {submitting ? 'Confirming...' : 'Force Confirm'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
