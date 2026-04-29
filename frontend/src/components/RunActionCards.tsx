import { useTranslation } from 'react-i18next'
import type { RunDetail } from '../api'
import ErrorBoundary from './common/ErrorBoundary'
import DownloadRunStateButton from './DownloadRunStateButton'

interface RunActionCardsProps {
  run: RunDetail
  runId: string
  onToggleReady: () => void
  toggleReadyPending: boolean
  onStartShopping: () => void
  startShoppingPending: boolean
  onFinishAdjusting: () => void
  onForceFinishAdjusting: () => void
  finishAdjustingPending: boolean
  onShowForceConfirmPopup: () => void
  onNavigateToShopping: () => void
}

export default function RunActionCards({
  run,
  runId,
  onToggleReady,
  toggleReadyPending,
  onStartShopping,
  startShoppingPending,
  onFinishAdjusting,
  onForceFinishAdjusting,
  finishAdjustingPending,
  onShowForceConfirmPopup,
  onNavigateToShopping,
}: RunActionCardsProps) {
  const { t } = useTranslation(['common', 'run'])

  return (
    <>
      {run.state === 'active' && (
        <ErrorBoundary>
          <div className="info-card">
            <h3>{t('run:labels.participants')}</h3>
            <div className="participants-list">
              {run.participants.map(participant => (
                <div key={participant.user_id} className="participant-item">
                  <div className="participant-info">
                    <span className={`participant-name ${participant.is_removed ? 'removed-user' : ''}`}>
                      {participant.user_name}
                      {participant.is_leader && <span className="leader-badge">{t('run:labels.leader')}</span>}
                      {participant.is_helper && <span className="helper-badge">{t('run:labels.helper')}</span>}
                    </span>
                  </div>
                  <div className="participant-ready">
                    {participant.is_ready ? (
                      <span className="ready-indicator ready">{t('run:labels.ready')}</span>
                    ) : (
                      <span className="ready-indicator not-ready">{t('run:labels.notReady')}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <div className="ready-section">
              <label className="ready-checkbox">
                <input
                  type="checkbox"
                  checked={run.current_user_is_ready}
                  onChange={onToggleReady}
                  disabled={toggleReadyPending}
                />
                <span>
                  {toggleReadyPending ? t('run:labels.updating') : t('run:labels.imReady')}
                </span>
              </label>
              <p className="ready-hint">{t('run:labels.readyHint')}</p>
            </div>
          </div>
        </ErrorBoundary>
      )}

      {run.state === 'active' && run.current_user_is_leader && (() => {
        const participantsWithBids = run.participants.filter(p =>
          run.products.some(product =>
            product.user_bids.some(bid => bid.user_id === p.user_id)
          )
        )
        const allReady = participantsWithBids.length > 0 && participantsWithBids.every(p => p.is_ready)

        return (
          <div className="info-card">
            {allReady ? (
              <>
                <h3>{t('run:labels.readyToConfirm')}</h3>
                <p>{t('run:labels.allParticipantsReady')}</p>
                <div className="flex-gap-md flex-wrap">
                  <button
                    onClick={onShowForceConfirmPopup}
                    className="btn btn-primary btn-lg"
                  >
                    {t('run:actions.proceedToConfirmed')}
                  </button>
                </div>
                <p className="ready-hint">
                  {t('run:labels.confirmRunHint')}
                </p>
              </>
            ) : (
              <>
                <h3>{t('run:labels.waitingForParticipants')}</h3>
                <p>{t('run:labels.notAllParticipantsReady')}</p>
                <p className="text-sm text-secondary mt-sm">
                  {t('run:labels.canForceConfirmIfNeeded')}{' '}
                  <button
                    onClick={onShowForceConfirmPopup}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--color-primary)',
                      textDecoration: 'underline',
                      cursor: 'pointer',
                      padding: 0,
                      font: 'inherit'
                    }}
                  >
                    {t('run:actions.forceConfirm')}
                  </button>
                </p>
              </>
            )}
          </div>
        )
      })()}

      {run.state === 'confirmed' && run.current_user_is_leader && (
        <div className="info-card">
          <h3>{t('run:labels.readyToShop')}</h3>
          <p>{t('run:labels.allParticipantsReady')}</p>
          <div className="flex-gap-md flex-wrap">
            <button
              onClick={onStartShopping}
              className="btn btn-primary btn-lg"
              disabled={startShoppingPending}
            >
              {startShoppingPending ? t('run:labels.starting') : t('run:actions.startShopping')}
            </button>
            <DownloadRunStateButton
              runId={runId}
              storeName={run.store_name}
              className="btn btn-secondary btn-lg"
            />
          </div>
          <p className="ready-hint">
            {t('run:labels.startShoppingHint')}
          </p>
        </div>
      )}

      {run.state === 'shopping' && (run.current_user_is_leader || run.current_user_is_helper) && (
        <div className="info-card">
          <h3>{t('run:labels.shoppingInProgress')}</h3>
          <p>{t('run:labels.currentlyShopping')}</p>
          <div className="flex-gap-md flex-wrap">
            <button
              onClick={onNavigateToShopping}
              className="btn btn-success btn-lg"
            >
              {t('run:actions.openShoppingList')}
            </button>
            <DownloadRunStateButton
              runId={runId}
              storeName={run.store_name}
              className="btn btn-secondary btn-lg"
            />
          </div>
          <p className="ready-hint">
            {t('run:labels.trackPricesHint')}
          </p>
        </div>
      )}

      {run.state === 'adjusting' && run.current_user_is_leader && (
        <div className="info-card">
          <h3>{t('run:labels.adjustingBids')}</h3>
          <p>{t('run:labels.adjustingBidsDescription')}</p>
          <div className="flex-gap-md flex-wrap">
            <button
              onClick={onFinishAdjusting}
              className="btn btn-primary btn-lg"
              disabled={finishAdjustingPending}
            >
              {finishAdjustingPending ? t('run:labels.processing') : t('run:actions.finishAdjusting')}
            </button>
            <button
              onClick={onForceFinishAdjusting}
              className="btn btn-secondary btn-lg"
              disabled={finishAdjustingPending}
            >
              {t('run:actions.forceFinish')}
            </button>
            <DownloadRunStateButton
              runId={runId}
              storeName={run.store_name}
              className="btn btn-secondary btn-lg"
            />
          </div>
          <p className="ready-hint">
            {t('run:labels.finishAdjustingHint')}
          </p>
        </div>
      )}
    </>
  )
}
