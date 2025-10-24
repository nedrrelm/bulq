import { useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { runsApi } from '../api'
import { runKeys } from '../hooks/queries'
import type { RunDetail } from '../api'
import '../styles/components/ManageHelpersPopup.css'
import { formatErrorForDisplay } from '../utils/errorHandling'

interface ManageHelpersPopupProps {
  run: RunDetail
  onClose: () => void
}

export default function ManageHelpersPopup({ run, onClose }: ManageHelpersPopupProps) {
  const [loadingUserId, setLoadingUserId] = useState<string | null>(null)
  const [error, setError] = useState<string>('')
  const queryClient = useQueryClient()

  // Filter out leader and removed participants
  const eligibleParticipants = run.participants.filter(
    p => !p.is_leader && !p.is_removed
  )

  // Handle ESC key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !loadingUserId) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose, loadingUserId])

  const handleToggleHelper = async (userId: string, isCurrentlyHelper: boolean) => {
    try {
      setLoadingUserId(userId)
      setError('')
      await runsApi.toggleHelper(run.id, userId)
      // Invalidate and refetch run details
      queryClient.invalidateQueries({ queryKey: runKeys.detail(run.id) })
    } catch (err) {
      setError(formatErrorForDisplay(err, isCurrentlyHelper ? 'remove helper' : 'add helper'))
    } finally {
      setLoadingUserId(null)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-md" onClick={(e) => e.stopPropagation()}>
        <h2>Manage Helpers</h2>
        <p className="text-sm" style={{ color: 'var(--color-text-light)', marginBottom: '1.5rem' }}>
          Helpers can add prices, mark items as purchased, and mark items as distributed.
        </p>

        {error && (
          <div className="error-message" style={{ marginBottom: '1rem' }}>
            {error}
          </div>
        )}

        {eligibleParticipants.length === 0 ? (
          <p className="text-center" style={{ color: 'var(--color-text-light)', padding: '2rem 0' }}>
            No other participants available to assign as helpers.
          </p>
        ) : (
          <div className="helpers-list">
            {eligibleParticipants.map(participant => (
              <div key={participant.user_id} className="helper-item">
                <div className="helper-info">
                  <span className="helper-name">{participant.user_name}</span>
                  {participant.is_helper && <span className="helper-badge-small">Helper</span>}
                </div>
                <button
                  type="button"
                  onClick={() => handleToggleHelper(participant.user_id, participant.is_helper)}
                  disabled={loadingUserId === participant.user_id}
                  className={participant.is_helper ? 'btn btn-secondary btn-sm' : 'btn btn-primary btn-sm'}
                >
                  {loadingUserId === participant.user_id
                    ? '...'
                    : participant.is_helper
                    ? '− Remove Helper'
                    : '+ Add Helper'}
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="button-group" style={{ marginTop: '1.5rem' }}>
          <button
            type="button"
            onClick={onClose}
            className="btn btn-secondary"
            disabled={!!loadingUserId}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
