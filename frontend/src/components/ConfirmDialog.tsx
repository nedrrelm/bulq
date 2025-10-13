import { useRef } from 'react'
import '../styles/components/ConfirmDialog.css'
import { useModalFocusTrap } from '../hooks/useModalFocusTrap'

interface ConfirmDialogProps {
  message: string
  onConfirm: () => void
  onCancel: () => void
  confirmText?: string
  cancelText?: string
  danger?: boolean
}

export default function ConfirmDialog({
  message,
  onConfirm,
  onCancel,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  danger = false
}: ConfirmDialogProps) {
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      onCancel()
    }
  }

  return (
    <div className="modal-overlay" onClick={onCancel} role="presentation">
      <div
        ref={modalRef}
        className="modal modal-sm confirm-dialog"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
        role="alertdialog"
        aria-labelledby="confirm-dialog-title"
        aria-describedby="confirm-dialog-message"
        aria-modal="true"
      >
        <h3 id="confirm-dialog-title">Confirm Action</h3>
        <p id="confirm-dialog-message" className="confirm-message">{message}</p>
        <div className="button-group">
          <button onClick={onCancel} className="btn btn-secondary">
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`}
            autoFocus
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
