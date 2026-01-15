/**
 * Format a quantity value to 2 decimal places, removing trailing zeros
 * @param value - The quantity to format
 * @returns Formatted string (e.g., 3.5, 5, 12.75)
 */
export function formatQuantity(value: number | null | undefined): string {
  if (value === null || value === undefined) return '0'
  // Round to 2 decimals and remove trailing zeros
  return parseFloat(value.toFixed(2)).toString()
}

/**
 * Format a price value to always show 2 decimal places
 * @param value - The price to format
 * @returns Formatted string (e.g., 3.50, 5.00, 12.75)
 */
export function formatPrice(value: number | null | undefined): string {
  if (value === null || value === undefined) return '0.00'
  return value.toFixed(2)
}
