import { useState, useEffect, useRef } from 'react'
import { groupsApi, ApiError } from '../api'
import type { Group } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'

interface NewGroupPopupProps {
  onClose: () => void
  onSuccess: (newGroup: Group) => void
}

export default function NewGroupPopup({ onClose, onSuccess }: NewGroupPopupProps) {
  const [groupName, setGroupName] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef)

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [onClose])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!groupName.trim()) {
      setError('Group name is required')
      return
    }

    try {
      setSubmitting(true)
      setError('')

      const newGroup = await groupsApi.createGroup({ name: groupName.trim() })
      onSuccess(newGroup)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create group')
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Create New Group</h2>
        </div>

        <form onSubmit={handleSubmit}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="group-name" className="form-label">Group Name</label>
            <input
              id="group-name"
              type="text"
              className="form-input"
              value={groupName}
              onChange={(e) => setGroupName(e.target.value)}
              placeholder="e.g., Friends & Family"
              autoFocus
              disabled={submitting}
            />
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
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Creating...' : 'Create Group'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
