import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { runsApi } from '../../api'
import { runKeys } from '../../hooks/queries'
import { getErrorMessage } from '../../utils/errorHandling'

interface EditCommentPopupProps {
  runId: string
  currentComment: string
  onClose: () => void
  onSuccess: () => void
}

export default function EditCommentPopup({
  runId,
  currentComment,
  onClose,
  onSuccess
}: EditCommentPopupProps) {
  const { t } = useTranslation(['common', 'run'])
  const [comment, setComment] = useState(currentComment)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const queryClient = useQueryClient()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await runsApi.updateComment(runId, { comment: comment.trim() || null })
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      onSuccess()
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to update comment'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal-sm" onClick={e => e.stopPropagation()}>
        <h3>{t('run:actions.editComment')}</h3>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="comment" className="form-label">{t('run:labels.comment')}</label>
            <textarea
              id="comment"
              className="form-input"
              value={comment}
              onChange={e => setComment(e.target.value)}
              placeholder={t('run:labels.commentPlaceholder')}
              disabled={loading}
              maxLength={500}
              rows={3}
              autoFocus
            />
            <span className="char-counter">{comment.length}/500</span>
          </div>
          <div className="button-group">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="btn btn-secondary"
            >
              {t('common:actions.cancel')}
            </button>
            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? t('common:actions.saving') : t('common:actions.save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
