/**
 * Utility for managing pending redirects and invite tokens in sessionStorage.
 * Used to preserve context when unauthenticated users need to login before
 * completing an action (e.g., joining a group via invite link).
 */

const PENDING_INVITE_KEY = 'pending_invite_token'
const REDIRECT_PATH_KEY = 'redirect_after_auth'

export const redirectStorage = {
  /**
   * Store an invite token to be processed after authentication
   */
  setPendingInvite(inviteToken: string): void {
    sessionStorage.setItem(PENDING_INVITE_KEY, inviteToken)
  },

  /**
   * Get the pending invite token
   */
  getPendingInvite(): string | null {
    return sessionStorage.getItem(PENDING_INVITE_KEY)
  },

  /**
   * Clear the pending invite token
   */
  clearPendingInvite(): void {
    sessionStorage.removeItem(PENDING_INVITE_KEY)
  },

  /**
   * Store a redirect path to navigate to after authentication
   */
  setRedirectPath(path: string): void {
    sessionStorage.setItem(REDIRECT_PATH_KEY, path)
  },

  /**
   * Get the redirect path
   */
  getRedirectPath(): string | null {
    return sessionStorage.getItem(REDIRECT_PATH_KEY)
  },

  /**
   * Clear the redirect path
   */
  clearRedirectPath(): void {
    sessionStorage.removeItem(REDIRECT_PATH_KEY)
  },

  /**
   * Clear all stored redirect data
   */
  clearAll(): void {
    sessionStorage.removeItem(PENDING_INVITE_KEY)
    sessionStorage.removeItem(REDIRECT_PATH_KEY)
  }
}
