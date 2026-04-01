/**
 * Query Key Factory Utilities
 *
 * This module provides utilities for creating consistent, type-safe query keys
 * for React Query. It eliminates duplication and ensures all query keys follow
 * the same hierarchical pattern.
 *
 * @example Basic usage
 * ```ts
 * const storeKeys = createQueryKeys('stores')
 * // Returns: { all, lists, list, details, detail }
 * ```
 *
 * @example With nested resources
 * ```ts
 * const groupKeys = createQueryKeys('groups', {
 *   nested: { runs: 'runs', members: 'members' }
 * })
 * // Returns: standard + runs(id), members(id)
 * ```
 *
 * @example With custom keys
 * ```ts
 * const notificationKeys = createQueryKeys('notifications', {
 *   custom: {
 *     unread: (base) => [...base, 'unread'] as const,
 *     count: (base) => [...base, 'count'] as const
 *   }
 * })
 * // Returns: standard + unread(), count()
 * ```
 *
 * @example With filters
 * ```ts
 * const productKeys = createQueryKeys('products', {
 *   filters: {
 *     byStore: (storeId: string) => ({ storeId })
 *   }
 * })
 * // Returns: standard + byStore(storeId)
 * ```
 */

/**
 * Options for customizing query key generation
 */
export interface QueryKeyOptions {
  /**
   * Nested resource definitions
   * Maps method names to resource names
   * @example { runs: 'runs', members: 'members' }
   */
  nested?: Record<string, string>

  /**
   * Custom key generators
   * Functions that take the base key and return a custom key array
   * @example { unread: (base) => [...base, 'unread'] as const }
   */
  custom?: Record<string, (base: readonly string[]) => readonly unknown[]>

  /**
   * Filter key generators
   * Functions that return filter objects for list queries
   * @example { byStore: (storeId: string) => ({ storeId }) }
   */
  filters?: Record<string, (...args: unknown[]) => unknown>
}

/**
 * Standard query keys returned by the factory
 */
export interface StandardQueryKeys<TEntity extends string> {
  /** Base key for all queries of this entity */
  readonly all: readonly [TEntity]
  /** Base key for all list queries */
  lists: () => readonly [TEntity, 'list']
  /** List query with optional filters */
  list: (filters?: unknown) => readonly [TEntity, 'list', unknown?]
  /** Base key for all detail queries */
  details: () => readonly [TEntity, 'detail']
  /** Detail query for a specific ID */
  detail: (id: string) => readonly [TEntity, 'detail', string]
}

/**
 * Nested resource keys
 */
export type NestedKeys<T extends Record<string, string>> = {
  [K in keyof T]: (id: string) => readonly unknown[]
}

/**
 * Custom keys
 */
export type CustomKeys<T extends Record<string, (base: readonly string[]) => readonly unknown[]>> = {
  [K in keyof T]: () => readonly unknown[]
}

/**
 * Filter keys
 */
export type FilterKeys<T extends Record<string, (...args: unknown[]) => unknown>> = {
  [K in keyof T]: (...args: Parameters<T[K]>) => readonly unknown[]
}

/**
 * Complete query keys type combining all features
 */
export type QueryKeys<
  TEntity extends string,
  TOptions extends QueryKeyOptions = QueryKeyOptions
> = StandardQueryKeys<TEntity> &
  (TOptions['nested'] extends Record<string, string> ? NestedKeys<TOptions['nested']> : Record<string, never>) &
  (TOptions['custom'] extends Record<string, (base: readonly string[]) => readonly unknown[]>
    ? CustomKeys<TOptions['custom']>
    : Record<string, never>) &
  (TOptions['filters'] extends Record<string, (...args: unknown[]) => unknown>
    ? FilterKeys<TOptions['filters']>
    : Record<string, never>)

/**
 * Create a set of query keys for an entity
 *
 * Generates a consistent set of query keys following the pattern:
 * - all: [entity]
 * - lists(): [entity, 'list']
 * - list(filters?): [entity, 'list', filters?]
 * - details(): [entity, 'detail']
 * - detail(id): [entity, 'detail', id]
 *
 * Plus any custom, nested, or filter keys specified in options.
 *
 * @param entity - The entity name (e.g., 'stores', 'products')
 * @param options - Optional configuration for nested, custom, and filter keys
 * @returns Object with all generated query key methods
 */
export function createQueryKeys<
  TEntity extends string,
  TOptions extends QueryKeyOptions = QueryKeyOptions
>(
  entity: TEntity,
  options?: TOptions
): QueryKeys<TEntity, TOptions> {
  // Base key for all queries of this entity
  const all = [entity] as const

  // Standard query keys
  const standard: StandardQueryKeys<TEntity> = {
    all,
    lists: () => [...all, 'list'] as const,
    list: (filters?: unknown) => {
      const base = [...all, 'list'] as const
      return filters !== undefined ? [...base, filters] as const : base
    },
    details: () => [...all, 'detail'] as const,
    detail: (id: string) => [...all, 'detail', id] as const,
  }

  // Generate nested resource keys
  const nested = options?.nested
    ? Object.entries(options.nested).reduce((acc, [key, value]) => ({
        ...acc,
        [key]: (id: string) => [...standard.detail(id), value] as const
      }), {} as NestedKeys<NonNullable<TOptions['nested']>>)
    : {}

  // Generate custom keys
  const custom = options?.custom
    ? Object.entries(options.custom).reduce((acc, [key, fn]) => ({
        ...acc,
        [key]: () => fn(all)
      }), {} as CustomKeys<NonNullable<TOptions['custom']>>)
    : {}

  // Generate filter keys
  const filters = options?.filters
    ? Object.entries(options.filters).reduce((acc, [key, fn]) => ({
        ...acc,
        [key]: (...args: unknown[]) => [...standard.lists(), fn(...args)] as const
      }), {} as FilterKeys<NonNullable<TOptions['filters']>>)
    : {}

  return {
    ...standard,
    ...nested,
    ...custom,
    ...filters
  } as QueryKeys<TEntity, TOptions>
}
