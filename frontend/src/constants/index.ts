/**
 * Application-wide constants
 */

// Form validation
export const MAX_NOTES_LENGTH = 200
export const MAX_NAME_LENGTH = 100
export const MAX_EMAIL_LENGTH = 255
export const MAX_PRODUCT_NAME_LENGTH = 100
export const MAX_STORE_NAME_LENGTH = 100
export const MAX_GROUP_NAME_LENGTH = 100

// WebSocket configuration
export const WEBSOCKET_RECONNECT_INTERVAL_MS = 3000
export const WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 5
export const WEBSOCKET_HEARTBEAT_INTERVAL_MS = 30000
export const WEBSOCKET_INITIAL_DELAY_MS = 100

// React Query configuration
export const QUERY_STALE_TIME_MS = 60000 // 1 minute
export const QUERY_CACHE_TIME_MS = 300000 // 5 minutes

// Run state ordering for display
export const RUN_STATE_ORDER: Record<string, number> = {
  'planning': 1,
  'active': 2,
  'confirmed': 3,
  'shopping': 4,
  'adjusting': 5,
  'distributing': 6,
  'completed': 7,
  'cancelled': 8
}

// UI timeouts and delays
export const TOAST_AUTO_HIDE_DELAY_MS = 3000
export const NAVIGATION_DELAY_AFTER_ACTION_MS = 1500 // Delay before navigating to let user see toast message
export const DEBOUNCE_SEARCH_MS = 300
export const FOCUS_DELAY_MS = 0 // Delay to ensure DOM is ready for focus

// Numeric constraints
export const MIN_BID_QUANTITY = 0
export const MAX_BID_QUANTITY = 9999
export const DECIMAL_PLACES_PRICE = 2
export const DECIMAL_PLACES_QUANTITY = 2
