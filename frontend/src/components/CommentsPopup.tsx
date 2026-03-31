import '../styles/components/CommentsPopup.css'
import { useTranslation } from 'react-i18next'
import type { UserBid } from '../schemas/run'
import BaseModal from './BaseModal'

interface CommentsPopupProps {
  productName: string
  userBids: UserBid[]
  currentUserId: string
  canEdit: boolean
  onClose: () => void
  onEditOwnBid: () => void
  onPlaceBid: () => void
}

export default function CommentsPopup({ productName, userBids, currentUserId, canEdit, onClose, onEditOwnBid, onPlaceBid }: CommentsPopupProps) {
  const { t } = useTranslation(['common', 'run'])

  // Filter bids that have comments
  const bidsWithComments = userBids.filter(bid => bid.comment && bid.comment.trim().length > 0)
  const currentUserBid = userBids.find(bid => bid.user_id === currentUserId)

  return (
    <BaseModal
      isOpen={true}
      onClose={onClose}
      size="md"
      className="comments-popup"
      asForm={false}
      showHeader={false}
      cancelButton={false}
      customActions={
        <>
          {canEdit && (
            currentUserBid ? (
              !currentUserBid.comment && (
                <button onClick={onEditOwnBid} className="btn btn-primary">
                  {t('run:comments.addYourComment')}
                </button>
              )
            ) : (
              <button onClick={onPlaceBid} className="btn btn-primary">
                {t('run:comments.placeBidAndComment')}
              </button>
            )
          )}
          <button onClick={onClose} className="btn btn-secondary">
            {t('common:actions.close')}
          </button>
        </>
      }
    >
      <h3>{t('run:comments.title', { product: productName })}</h3>

      {bidsWithComments.length === 0 ? (
        <div className="no-comments">
          <p>{t('run:comments.noComments')}</p>
        </div>
      ) : (
        <div className="comments-list">
          {bidsWithComments.map((bid) => {
            const isCurrentUser = bid.user_id === currentUserId
            return (
              <div key={bid.user_id} className={`comment-item ${isCurrentUser ? 'own-comment' : ''}`}>
                <div className="comment-header">
                  <div className="comment-user-info">
                    <span className="user-name">{bid.user_name}</span>
                    <span className="user-quantity">({t('run:comments.itemCount', { count: bid.quantity })})</span>
                  </div>
                  {isCurrentUser && canEdit && (
                    <button
                      onClick={onEditOwnBid}
                      className="edit-comment-button"
                      title={t('run:comments.editTooltip')}
                    >
                      ✏️ {t('common:actions.edit')}
                    </button>
                  )}
                </div>
                <div className="comment-text">{bid.comment}</div>
              </div>
            )
          })}
        </div>
      )}
    </BaseModal>
  )
}
