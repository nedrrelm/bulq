import { useState, useRef } from 'react'
import { groupsApi, ApiError } from '../api'
import type { Group } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { validateLength, validateAlphanumeric, sanitizeString } from '../utils/validation'

interface NewGroupPopupProps {
  onClose: () => void
  onSuccess: (newGroup: Group) => void
}

const MAX_LENGTH = 100
const MIN_LENGTH = 2

export default function NewGroupPopup({ onClose, onSuccess }: NewGroupPopupProps) {
  const [groupName, setGroupName] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

  const validateGroupName = (value: string): boolean => {
    setError('')

    const trimmed = value.trim()

    if (trimmed.length === 0) {
      setError('Group name is required')
      return false
    }

    const lengthValidation = validateLength(trimmed, MIN_LENGTH, MAX_LENGTH, 'Group name')
    if (!lengthValidation.isValid) {
      setError(lengthValidation.error || 'Invalid group name')
      return false
    }

    const alphanumericValidation = validateAlphanumeric(trimmed, '- _&\'', 'Group name')
    if (!alphanumericValidation.isValid) {
      setError(alphanumericValidation.error || 'Group name contains invalid characters')
      return false
    }

    return true
  }

  const handleNameChange = (value: string) => {
    // Limit input to max length
    const sanitized = sanitizeString(value, MAX_LENGTH)
    setGroupName(sanitized)
    setError('') // Clear error on change
  }

  const handleBlur = () => {
    if (groupName.trim()) {
      validateGroupName(groupName)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateGroupName(groupName)) {
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

  const charCount = groupName.length

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
            <label htmlFor="group-name" className="form-label">Group Name *</label>
            <input
              id="group-name"
              type="text"
              className={`form-input ${error ? 'input-error' : ''}`}
              value={groupName}
              onChange={(e) => handleNameChange(e.target.value)}
              onBlur={handleBlur}
              placeholder="e.g., Friends & Family"
              autoFocus
              disabled={submitting}
            />
            <small className="input-hint">
              Use letters, numbers, spaces, and - _ & '
            </small>
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
