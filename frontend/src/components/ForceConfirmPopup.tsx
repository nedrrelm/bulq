import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { runsApi } from '../api'
import { getErrorMessage } from '../utils/errorHandling'
import BaseModal from './BaseModal'

interface ForceConfirmPopupProps {
  runId: string
  onClose: () => void
  onSuccess: () => void
}

export default function ForceConfirmPopup({ runId, onClose, onSuccess }: ForceConfirmPopupProps) {
  const { t } = useTranslation(['common', 'run'])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

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
    <BaseModal
      isOpen={true}
      onClose={onClose}
      title={t('run:forceConfirm.title')}
      error={error}
      submitButton={{
        text: submitting ? t('run:actions.confirming') : t('run:actions.forceConfirm'),
        onClick: handleForceConfirm,
        variant: 'warning',
        loading: submitting,
        disabled: submitting
      }}
    >
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
    </BaseModal>
  )
}
