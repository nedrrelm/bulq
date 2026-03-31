import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { MergeResponse } from '../../api/adminFactory'
import { translateSuccess } from '../../utils/translation'
import { getErrorMessage } from '../../utils/errorHandling'

/**
 * Supported entity types for merge operations
 */
export type AdminEntityType = 'user' | 'product' | 'store'

/**
 * Props for AdminMergeSection component
 */
export interface AdminMergeSectionProps {
  /**
   * Type of entity being merged (used for i18n keys)
   */
  entityType: AdminEntityType

  /**
   * ID of the source entity (the one being merged into target)
   */
  entityId: string

  /**
   * Display name of the source entity (shown in confirmation dialog)
   */
  entityName: string

  /**
   * Function to perform the merge operation
   * @param sourceId - ID of source entity (same as entityId)
   * @param targetId - ID of target entity to merge into
   * @returns Promise resolving to merge response
   */
  mergeHandler: (sourceId: string, targetId: string) => Promise<MergeResponse>

  /**
   * Callback invoked after successful merge
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
   * If not provided, merge will execute without confirmation
   */
  showConfirm?: (message: string, onConfirm: () => void) => void
}

/**
 * Reusable merge section component for admin edit popups
 *
 * Provides a standardized UI and logic for merging admin entities.
 * Includes input field for target ID, validation, confirmation dialog,
 * and success/error handling.
 *
 * @example
 * ```tsx
 * <AdminMergeSection
 *   entityType="product"
 *   entityId={product.id}
 *   entityName={product.name}
 *   mergeHandler={adminApi.mergeProducts}
 *   onSuccess={onSuccess}
 *   onError={setError}
 *   disabled={submitting}
 *   showConfirm={showConfirm}
 * />
 * ```
 */
export function AdminMergeSection({
  entityType,
  entityId,
  entityName,
  mergeHandler,
  onSuccess,
  onError,
  disabled = false,
  showConfirm
}: AdminMergeSectionProps) {
  const { t } = useTranslation(['admin', 'common'])
  const [mergeTargetId, setMergeTargetId] = useState('')
  const [loading, setLoading] = useState(false)

  const handleMerge = async () => {
    // Validate target ID
    if (!mergeTargetId.trim()) {
      onError?.(t(`admin:edit.${entityType}.errors.mergeTargetRequired`))
      return
    }

    try {
      setLoading(true)

      // Perform merge
      const response = await mergeHandler(entityId, mergeTargetId.trim())

      // Show success message
      const successMsg = translateSuccess(response.code, response.details)
      alert(`${successMsg}\n${t('admin:edit.affectedRecords')}: ${response.affected_records}`)

      // Notify parent of success
      onSuccess()
    } catch (err) {
      // Handle error
      const errorMsg = getErrorMessage(err, t(`admin:edit.${entityType}.errors.mergeFailed`))
      onError?.(errorMsg)
      setLoading(false)
    }
  }

  const handleMergeClick = () => {
    if (showConfirm) {
      // Show confirmation dialog
      showConfirm(
        t(`admin:edit.${entityType}.mergeConfirm`, { name: entityName }),
        handleMerge
      )
    } else {
      // Execute immediately if no confirmation dialog
      handleMerge()
    }
  }

  return (
    <div className="form-group">
      <label htmlFor="merge-target" className="form-label">
        {t(`admin:edit.${entityType}.mergeTitle`)}
      </label>
      <p className="text-description mb-sm">
        {t(`admin:edit.${entityType}.mergeDescription`)}
      </p>
      <div className="flex-gap-sm">
        <input
          id="merge-target"
          type="text"
          className="form-input"
          value={mergeTargetId}
          onChange={(e) => {
            setMergeTargetId(e.target.value)
            // Clear error when user types
            if (onError) onError('')
          }}
          placeholder={t(`admin:edit.${entityType}.mergePlaceholder`)}
          disabled={disabled || loading}
        />
        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleMergeClick}
          disabled={disabled || loading || !mergeTargetId.trim()}
        >
          {loading ? t('common:loading') : t(`admin:edit.${entityType}.mergeButton`)}
        </button>
      </div>
    </div>
  )
}
