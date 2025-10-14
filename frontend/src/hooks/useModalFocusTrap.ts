import { useEffect, type RefObject } from 'react'

const FOCUSABLE_SELECTOR = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'

/**
 * Traps focus within a modal dialog for accessibility.
 * Ensures Tab and Shift+Tab cycle through focusable elements within the modal.
 * Closes modal on Escape key press.
 *
 * @param modalRef - Reference to the modal container element
 * @param isOpen - Whether the modal is currently open
 * @param onClose - Optional callback to close the modal on Escape key
 */
export function useModalFocusTrap(
  modalRef: RefObject<HTMLElement | null>,
  isOpen: boolean = true,
  onClose?: () => void
) {
  useEffect(() => {
    if (!isOpen || !modalRef.current) return

    const modalElement = modalRef.current
    const focusableElements = modalElement.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)
    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    // Store the element that had focus before the modal opened
    const previouslyFocusedElement = document.activeElement as HTMLElement

    // Focus the first element when modal opens
    if (firstElement) {
      firstElement.focus()
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      // Handle Escape key
      if (e.key === 'Escape' && onClose) {
        e.preventDefault()
        onClose()
        return
      }

      // Handle Tab key
      if (e.key !== 'Tab') return

      // If only one focusable element, prevent tabbing
      if (focusableElements.length === 1) {
        e.preventDefault()
        return
      }

      // Shift + Tab (backwards)
      if (e.shiftKey) {
        if (document.activeElement === firstElement && lastElement) {
          e.preventDefault()
          lastElement.focus()
        }
      }
      // Tab (forwards)
      else {
        if (document.activeElement === lastElement && firstElement) {
          e.preventDefault()
          firstElement.focus()
        }
      }
    }

    modalElement.addEventListener('keydown', handleKeyDown)

    // Cleanup: restore focus to previous element when modal closes
    return () => {
      modalElement.removeEventListener('keydown', handleKeyDown)
      if (previouslyFocusedElement && previouslyFocusedElement.focus) {
        previouslyFocusedElement.focus()
      }
    }
  }, [modalRef, isOpen, onClose])
}
