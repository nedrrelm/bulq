import { ReactNode } from 'react'
import Toast from './Toast'
import ConfirmDialog from './ConfirmDialog'
import { useToast } from '../hooks/useToast'
import { useConfirm } from '../hooks/useConfirm'

interface PageLayoutProps {
  children: ReactNode
}

/**
 * PageLayout - Wrapper component that provides common functionality to all pages
 *
 * This component:
 * - Provides toast notifications
 * - Provides confirmation dialogs
 * - Reduces code duplication across page components
 *
 * Usage:
 * ```tsx
 * export default function MyPage() {
 *   const { showToast } = useToast()
 *   const { showConfirm } = useConfirm()
 *
 *   return (
 *     <PageLayout>
 *       <div className="my-page">
 *         // page content
 *       </div>
 *     </PageLayout>
 *   )
 * }
 * ```
 */
export default function PageLayout({ children }: PageLayoutProps) {
  const { toast, hideToast } = useToast()
  const { confirmState, hideConfirm, handleConfirm } = useConfirm()

  return (
    <>
      {children}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={hideToast}
          duration={toast.duration}
        />
      )}

      {confirmState.isOpen && (
        <ConfirmDialog
          message={confirmState.message}
          onConfirm={handleConfirm}
          onCancel={hideConfirm}
          danger={confirmState.danger}
        />
      )}
    </>
  )
}
