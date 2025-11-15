import { useTranslation } from 'react-i18next'

interface ErrorAlertProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorAlert({ message, onRetry }: ErrorAlertProps) {
  const { t } = useTranslation(['common'])

  return (
    <div className="alert alert-error">
      <p>{message}</p>
      {onRetry && (
        <button className="btn btn-secondary" onClick={onRetry}>
          {t('common:buttons.retry')}
        </button>
      )}
    </div>
  );
}
