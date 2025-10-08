import { useState, useCallback } from 'react'

interface ConfirmState {
  message: string
  onConfirm: () => void
  confirmText?: string
  cancelText?: string
  danger?: boolean
}

export function useConfirm() {
  const [confirmState, setConfirmState] = useState<ConfirmState | null>(null)

  const showConfirm = useCallback((
    message: string,
    onConfirm: () => void,
    options?: { confirmText?: string; cancelText?: string; danger?: boolean }
  ) => {
    setConfirmState({
      message,
      onConfirm,
      ...options
    })
  }, [])

  const hideConfirm = useCallback(() => {
    setConfirmState(null)
  }, [])

  const handleConfirm = useCallback(() => {
    if (confirmState) {
      confirmState.onConfirm()
      hideConfirm()
    }
  }, [confirmState, hideConfirm])

  return { confirmState, showConfirm, hideConfirm, handleConfirm }
}
