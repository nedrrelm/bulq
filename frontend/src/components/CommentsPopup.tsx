import { useRef, useEffect } from 'react'
import '../styles/components/CommentsPopup.css'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'
import type { UserBid } from '../schemas/run'

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
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, true, onClose)

  // Filter bids that have comments
  const bidsWithComments = userBids.filter(bid => bid.comment && bid.comment.trim().length > 0)

  // Handle escape key globally
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  const currentUserBid = userBids.find(bid => bid.user_id === currentUserId)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={modalRef}
        className="modal modal-md comments-popup"
        onClick={(e) => e.stopPropagation()}
      >
        <h3>Comments for {productName}</h3>

        {bidsWithComments.length === 0 ? (
          <div className="no-comments">
            <p>No comments yet for this product.</p>
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
                      <span className="user-quantity">({bid.quantity} {bid.quantity === 1 ? 'item' : 'items'})</span>
                    </div>
                    {isCurrentUser && canEdit && (
                      <button
                        onClick={onEditOwnBid}
                        className="edit-comment-button"
                        title="Edit your bid and comment"
                      >
                        ✏️ Edit
                      </button>
                    )}
                  </div>
                  <div className="comment-text">{bid.comment}</div>
                </div>
              )
            })}
          </div>
        )}

        <div className="button-group">
          {canEdit && (
            currentUserBid ? (
              !currentUserBid.comment && (
                <button onClick={onEditOwnBid} className="btn btn-primary">
                  Add Your Comment
                </button>
              )
            ) : (
              <button onClick={onPlaceBid} className="btn btn-primary">
                Place Bid & Add Comment
              </button>
            )
          )}
          <button onClick={onClose} className="btn btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
