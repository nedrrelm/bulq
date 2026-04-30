import { useRef, type ReactNode, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useModalFocusTrap } from '../../hooks/useModalFocusTrap'

export interface BaseModalAction {
  text: string
  onClick: (e: FormEvent) => void | Promise<void>
  variant?: 'primary' | 'secondary' | 'success' | 'danger' | 'warning'
  loading?: boolean
  disabled?: boolean
  type?: 'button' | 'submit'
}

export interface BaseModalProps {
  /** Whether the modal is open */
  isOpen: boolean
  /** Callback when modal should close */
  onClose: () => void
  /** Optional modal title (shown in header) */
  title?: string
  /** Optional error message to display */
  error?: string
  /** Modal size variant */
  size?: 'sm' | 'md' | 'lg' | 'scrollable'
  /** Modal content */
  children: ReactNode
  /** Submit button configuration */
  submitButton?: BaseModalAction
  /** Cancel button configuration (defaults to standard cancel) */
  cancelButton?: BaseModalAction | false
  /** Additional custom action buttons */
  customActions?: ReactNode
  /** Additional CSS class for modal content */
  className?: string
  /** Show header with title (default: true if title provided) */
  showHeader?: boolean
  /** Render as a form element (default: true) */
  asForm?: boolean
}

/**
 * Base modal component that provides consistent modal behavior across the app.
 *
 * Features:
 * - Automatic focus trap with escape key handling
 * - Click-outside-to-close
 * - Built-in error display
 * - Configurable action buttons
 * - Multiple size variants
 * - Optional form wrapper
 *
 * @example
 * ```tsx
 * <BaseModal
 *   isOpen={isOpen}
 *   onClose={handleClose}
 *   title="Edit Product"
 *   error={error}
 *   submitButton={{
 *     text: 'Save',
 *     onClick: handleSubmit,
 *     loading: submitting
 *   }}
 * >
 *   <div className="form-group">
 *     <label>Product Name</label>
 *     <input type="text" value={name} onChange={...} />
 *   </div>
 * </BaseModal>
 * ```
 */
export default function BaseModal({
  isOpen,
  onClose,
  title,
  error,
  size = 'md',
  children,
  submitButton,
  cancelButton,
  customActions,
  className = '',
  showHeader = !!title,
  asForm = true
}: BaseModalProps) {
  const { t } = useTranslation(['common'])
  const modalRef = useRef<HTMLDivElement>(null)

  useModalFocusTrap(modalRef, isOpen, onClose)

  if (!isOpen) return null

  // Determine modal size class
  const sizeClass = size === 'scrollable' ? 'modal modal-scrollable' : `modal modal-${size}`

  // Build class name
  const modalClassName = `${sizeClass} ${className}`.trim()

  // Handle form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (submitButton?.onClick) {
      await submitButton.onClick(e)
    }
  }

  // Handle cancel button
  const handleCancel = (e: FormEvent) => {
    if (cancelButton && cancelButton !== false && cancelButton.onClick) {
      cancelButton.onClick(e)
    } else {
      onClose()
    }
  }

  // Determine if we have any actions to display
  const hasActions = submitButton || cancelButton !== false || customActions

  // Get button class based on variant
  const getButtonClass = (variant: BaseModalAction['variant'] = 'primary') => {
    return `btn btn-${variant}`
  }

  const ContentWrapper = asForm ? 'form' : 'div'

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        ref={modalRef}
        className={modalClassName}
        onClick={(e) => e.stopPropagation()}
      >
        {showHeader && title && (
          <div className="modal-header">
            <h2>{title}</h2>
          </div>
        )}

        <ContentWrapper {...(asForm ? { onSubmit: handleSubmit } : {})}>
          {error && (
            <div className="alert alert-error">
              {error}
            </div>
          )}

          {children}

          {hasActions && (
            <div className="modal-actions">
              {cancelButton !== false && (
                <button
                  type="button"
                  className={getButtonClass(cancelButton?.variant || 'secondary')}
                  onClick={handleCancel}
                  disabled={cancelButton?.disabled || submitButton?.loading}
                >
                  {cancelButton?.text || t('common:buttons.cancel')}
                </button>
              )}

              {customActions}

              {submitButton && (
                <button
                  type={submitButton.type || (asForm ? 'submit' : 'button')}
                  className={getButtonClass(submitButton.variant || 'primary')}
                  onClick={asForm ? undefined : submitButton.onClick}
                  disabled={submitButton.disabled || submitButton.loading}
                >
                  {submitButton.text}
                </button>
              )}
            </div>
          )}
        </ContentWrapper>
      </div>
    </div>
  )
}
