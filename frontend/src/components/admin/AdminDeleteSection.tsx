import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { DeleteResponse } from '../../api/adminFactory'
import { translateSuccess } from '../../utils/translation'
import { getErrorMessage } from '../../utils/errorHandling'
import type { AdminEntityType } from './AdminMergeSection'

/**
 * Props for AdminDeleteSection component
 */
export interface AdminDeleteSectionProps {
  /**
   * Type of entity being deleted (used for i18n keys)
   */
  entityType: AdminEntityType

  /**
   * ID of the entity to delete
   */
  entityId: string

  /**
   * Display name of the entity (shown in confirmation dialog)
   */
  entityName: string

  /**
   * Function to perform the delete operation
   * @param id - ID of entity to delete
   * @returns Promise resolving to delete response
   */
  deleteHandler: (id: string) => Promise<DeleteResponse>

  /**
   * Callback invoked after successful deletion
   */
  onSuccess: () => void

  /**
   * Optional callback for error handling
   * @param error - Error message to display
   */
  onError?: (error: string) => void

  /**
   * Whether the form is disabled (e.g., during submission)
   * @default false
   */
  disabled?: boolean

  /**
   * Function to show confirmation dialog
   * If not provided, delete will execute without confirmation
   */
  showConfirm?: (message: string, onConfirm: () => void, options?: { danger?: boolean }) => void
}

/**
 * Reusable delete section component for admin edit popups
 *
 * Provides a standardized "danger zone" UI and logic for deleting admin entities.
 * Includes warning message, confirmation dialog, and success/error handling.
 *
 * @example
 * ```tsx
 * <AdminDeleteSection
 *   entityType="product"
 *   entityId={product.id}
 *   entityName={product.name}
 *   deleteHandler={adminApi.deleteProduct}
 *   onSuccess={onSuccess}
 *   onError={setError}
 *   disabled={submitting}
 *   showConfirm={showConfirm}
 * />
 * ```
 */
export function AdminDeleteSection({
  entityType,
  entityId,
  entityName,
  deleteHandler,
  onSuccess,
  onError,
  disabled = false,
  showConfirm
}: AdminDeleteSectionProps) {
  const { t } = useTranslation(['admin', 'common'])
  const [loading, setLoading] = useState(false)

  const handleDelete = async () => {
    try {
      setLoading(true)

      // Perform delete
      const response = await deleteHandler(entityId)

      // Show success message
      alert(translateSuccess(response.code, response.details))

      // Notify parent of success
      onSuccess()
    } catch (err) {
      // Handle error
      const errorMsg = getErrorMessage(err, 'Failed to delete ' + entityType)
      onError?.(errorMsg)
      setLoading(false)
    }
  }

  const handleDeleteClick = () => {
    if (showConfirm) {
      // Show confirmation dialog with danger flag
      showConfirm(
        t(`admin:edit.${entityType}.deleteConfirm`, { name: entityName }),
        handleDelete,
        { danger: true }
      )
    } else {
      // Execute immediately if no confirmation dialog
      handleDelete()
    }
  }

  return (
    <div className="form-group">
      <label className="form-label label-danger">
        {t('admin:edit.dangerZone')}
      </label>
      <p className="text-description mb-sm">
        {t(`admin:edit.${entityType}.deleteWarning`)}
      </p>
      <button
        type="button"
        className="btn btn-danger"
        onClick={handleDeleteClick}
        disabled={disabled || loading}
      >
        {loading ? t('common:loading') : t(`admin:edit.${entityType}.deleteButton`)}
      </button>
    </div>
  )
}
