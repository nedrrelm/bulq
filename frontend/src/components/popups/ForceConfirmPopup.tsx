import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { runsApi } from '../../api'
import { getErrorMessage } from '../../utils/errorHandling'
import BaseModal from '../common/BaseModal'

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
      <div className="mb-lg">
        <p className="mb-md">
          <strong>{t('run:forceConfirm.warning')}</strong> {t('run:forceConfirm.warningDescription')}
        </p>
        <p className="mb-md text-secondary">
          {t('run:forceConfirm.useThisIf')}
        </p>
        <ul className="list-secondary">
          <li>{t('run:forceConfirm.reason1')}</li>
          <li>{t('run:forceConfirm.reason2')}</li>
          <li>{t('run:forceConfirm.reason3')}</li>
        </ul>
        <p className="mt-md text-description">
          {t('run:forceConfirm.consequence')}
        </p>
      </div>
    </BaseModal>
  )
}
