import { useTranslation } from 'react-i18next'

export default function LoadingSpinner() {
  const { t } = useTranslation(['common'])

  return (
    <div className="loading-spinner-container">
      <div className="loading-spinner"></div>
      <p>{t('common:states.loading')}</p>
    </div>
  );
}
