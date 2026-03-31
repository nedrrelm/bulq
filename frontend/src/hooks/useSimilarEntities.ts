import { useState, useEffect } from 'react'

/**
 * Base entity interface - all entities must have an id and name
 */
export interface Entity {
  id: string
  name: string
}

/**
 * Configuration options for useSimilarEntities hook
 */
export interface UseSimilarEntitiesOptions<T extends Entity> {
  /**
   * The search value to check for similar entities
   */
  searchValue: string

  /**
   * Async function that fetches similar entities from the API
   * @param value - The trimmed search value
   * @returns Promise resolving to array of similar entities
   */
  fetcher: (value: string) => Promise<T[]>

  /**
   * Minimum length required before triggering the similarity check
   * @default 2
   */
  minLength?: number

  /**
   * Debounce delay in milliseconds before calling the fetcher
   * @default 300
   */
  debounceMs?: number

  /**
   * Optional function to extract comparison value from entity
   * Used for exact match detection with custom logic
   * @param entity - The entity to extract comparison value from
   * @returns String to compare (will be lowercased for comparison)
   * @default (entity) => entity.name
   */
  getComparisonValue?: (entity: T) => string

  /**
   * Optional function to extract comparison value from current input
   * Used for exact match detection with custom logic
   * @param searchValue - The current search value (trimmed)
   * @returns String to compare (will be lowercased for comparison)
   * @default (searchValue) => searchValue
   */
  getInputComparisonValue?: (searchValue: string) => string
}

/**
 * Result returned by useSimilarEntities hook
 */
export interface UseSimilarEntitiesResult<T extends Entity> {
  /**
   * Array of similar entities found
   */
  similar: T[]

  /**
   * The entity that exactly matches the search value (case-insensitive)
   * undefined if no exact match found
   */
  exactMatch: T | undefined

  /**
   * True if there are similar entities but none are exact matches
   */
  hasNonExactSimilar: boolean

  /**
   * True while the API call is in flight
   */
  loading: boolean
}

/**
 * Hook for checking similar entities with debouncing
 *
 * This hook handles the common pattern of checking for similar entities
 * as the user types, with configurable debouncing and minimum length validation.
 * It's designed to prevent duplicate entries and provide helpful suggestions.
 *
 * @example Simple usage with stores
 * ```typescript
 * const { similar, exactMatch, hasNonExactSimilar } = useSimilarEntities({
 *   searchValue: storeName,
 *   fetcher: storesApi.checkSimilar
 * })
 * ```
 *
 * @example Advanced usage with products (matching name and brand)
 * ```typescript
 * const { similar, exactMatch, hasNonExactSimilar } = useSimilarEntities({
 *   searchValue: productName,
 *   fetcher: productsApi.checkSimilar,
 *   getComparisonValue: (product) =>
 *     `${product.name}|${product.brand || ''}`.toLowerCase(),
 *   getInputComparisonValue: (name) =>
 *     `${name}|${brand}`.toLowerCase()
 * })
 * ```
 *
 * @param options - Configuration options
 * @returns Object containing similar entities, exact match, and computed flags
 */
export function useSimilarEntities<T extends Entity>({
  searchValue,
  fetcher,
  minLength = 2,
  debounceMs = 300,
  getComparisonValue,
  getInputComparisonValue
}: UseSimilarEntitiesOptions<T>): UseSimilarEntitiesResult<T> {
  const [similar, setSimilar] = useState<T[]>([])
  const [loading, setLoading] = useState(false)

  // Default comparison functions
  const defaultGetComparison = (entity: T) => entity.name.toLowerCase()
  const defaultGetInputComparison = (value: string) => value.toLowerCase()

  const compareEntity = getComparisonValue || defaultGetComparison
  const compareInput = getInputComparisonValue || defaultGetInputComparison

  // Effect to check for similar entities with debouncing
  useEffect(() => {
    const checkSimilar = async () => {
      const trimmed = searchValue.trim()

      // Only check if we have at least minLength characters
      if (trimmed.length < minLength) {
        setSimilar([])
        setLoading(false)
        return
      }

      setLoading(true)

      try {
        const results = await fetcher(trimmed)
        setSimilar(results)
      } catch (err) {
        // Silently fail - this is a nice-to-have feature
        // We don't want to disrupt the user experience if the API fails
        setSimilar([])
      } finally {
        setLoading(false)
      }
    }

    // Debounce the API call
    const timeoutId = setTimeout(checkSimilar, debounceMs)

    // Cleanup timeout on unmount or when searchValue changes
    return () => clearTimeout(timeoutId)
  }, [searchValue, minLength, debounceMs, fetcher])

  // Compute exact match
  const trimmedSearch = searchValue.trim()
  const inputComparison = compareInput(trimmedSearch)

  const exactMatch = similar.find(
    entity => compareEntity(entity) === inputComparison
  )

  // Check if there are similar entities that are not exact matches
  const hasNonExactSimilar = similar.length > 0 && !exactMatch

  return {
    similar,
    exactMatch,
    hasNonExactSimilar,
    loading
  }
}
