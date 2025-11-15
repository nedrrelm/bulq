import { useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { runsApi } from '../api'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import { getErrorMessage } from '../utils/errorHandling'

interface ForceConfirmPopupProps {
  runId: string
  onClose: () => void
  onSuccess: () => void
}

export default function ForceConfirmPopup({ runId, onClose, onSuccess }: ForceConfirmPopupProps) {
  const { t } = useTranslation(['common', 'run'])
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
      setError(getErrorMessage(err, t('run:errors.forceConfirmFailed')))
      setSubmitting(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div ref={modalRef} className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{t('run:forceConfirm.title')}</h2>
        </div>

        <form onSubmit={handleForceConfirm}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          <div style={{ marginBottom: '1.5rem' }}>
            <p style={{ marginBottom: '1rem' }}>
              <strong>{t('run:forceConfirm.warning')}</strong> {t('run:forceConfirm.warningDescription')}
            </p>
            <p style={{ marginBottom: '1rem', color: 'var(--color-text-secondary)' }}>
              {t('run:forceConfirm.useThisIf')}
            </p>
            <ul style={{ marginLeft: '1.5rem', color: 'var(--color-text-secondary)' }}>
              <li>{t('run:forceConfirm.reason1')}</li>
              <li>{t('run:forceConfirm.reason2')}</li>
              <li>{t('run:forceConfirm.reason3')}</li>
            </ul>
            <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
              {t('run:forceConfirm.consequence')}
            </p>
          </div>

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={submitting}
            >
              {t('common:buttons.cancel')}
            </button>
            <button
              type="submit"
              className="btn"
              style={{ backgroundColor: 'var(--color-warning)', color: 'white' }}
              disabled={submitting}
            >
              {submitting ? t('run:actions.confirming') : t('run:actions.forceConfirm')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
