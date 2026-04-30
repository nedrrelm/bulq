import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useTranslation } from 'react-i18next'
import { runsApi } from '../../api'
import { runKeys } from '../../hooks/queries'
import { getErrorMessage } from '../../utils/errorHandling'
import BaseModal from '../common/BaseModal'

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
    <BaseModal
      isOpen={true}
      onClose={onClose}
      title={t('run:actions.editComment')}
      error={error}
      size="sm"
      submitButton={{
        text: loading ? t('common:actions.saving') : t('common:actions.save'),
        onClick: handleSubmit,
        loading: loading,
        disabled: loading,
      }}
      cancelButton={{
        text: t('common:actions.cancel'),
        onClick: onClose,
        disabled: loading,
      }}
    >
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
    </BaseModal>
  )
}
