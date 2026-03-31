import { api } from './client'

/**
 * Base interface for admin entities
 * All admin entities must have these fields
 */
export interface AdminEntity {
  id: string
  verified?: boolean
  created_at: string
}

/**
 * Options for querying admin entities
 */
export interface GetAdminEntitiesOptions {
  search?: string
  verified?: boolean
  limit?: number
  offset?: number
}

/**
 * Response from merge operation
 */
export interface MergeResponse {
  success: boolean
  code: string
  source_id: string
  target_id: string
  affected_records: number
  details?: Record<string, any>
}

/**
 * Response from delete operation
 */
export interface DeleteResponse {
  success: boolean
  code: string
  deleted_id: string
  details?: Record<string, any>
}

/**
 * Options for creating admin entity API
 */
export interface AdminEntityApiOptions {
  /**
   * Whether this entity supports verification
   * If true, generates toggleVerification() method
   * @default true
   */
  hasVerification?: boolean
}

/**
 * Standard admin CRUD operations for an entity
 */
export interface AdminEntityApi<
  TEntity extends AdminEntity,
  TUpdateData extends Record<string, any> = Record<string, any>
> {
  /**
   * Get all entities with optional filtering
   */
  getAll: (
    search?: string,
    verified?: boolean,
    limit?: number,
    offset?: number
  ) => Promise<TEntity[]>

  /**
   * Toggle verification status of an entity
   * Only available if hasVerification: true
   */
  toggleVerification?: (id: string) => Promise<TEntity>

  /**
   * Update an entity
   */
  update: (id: string, data: TUpdateData) => Promise<TEntity>

  /**
   * Merge source entity into target entity
   * All references to source will be updated to target
   */
  merge: (sourceId: string, targetId: string) => Promise<MergeResponse>

  /**
   * Delete an entity
   */
  delete: (id: string) => Promise<DeleteResponse>
}

/**
 * Create a standardized admin entity API with CRUD operations
 *
 * This factory generates consistent API methods for managing admin entities.
 * It eliminates code duplication and ensures all admin entities follow the
 * same patterns for CRUD operations.
 *
 * @example Basic usage for stores
 * ```typescript
 * const storesAdmin = createAdminEntityApi<AdminStore>('stores')
 * // Returns: { getAll, toggleVerification, update, merge, delete }
 * ```
 *
 * @example Without verification support
 * ```typescript
 * const groupsAdmin = createAdminEntityApi<AdminGroup>('groups', {
 *   hasVerification: false
 * })
 * // Returns: { getAll, update, merge, delete }
 * // Note: no toggleVerification method
 * ```
 *
 * @param entityPath - The API path segment for this entity (e.g., 'users', 'products')
 * @param options - Configuration options
 * @returns Object with all admin CRUD methods for this entity
 */
export function createAdminEntityApi<
  TEntity extends AdminEntity,
  TUpdateData extends Record<string, any> = Record<string, any>
>(
  entityPath: string,
  options: AdminEntityApiOptions = {}
): AdminEntityApi<TEntity, TUpdateData> {
  const { hasVerification = true } = options

  const api_methods: AdminEntityApi<TEntity, TUpdateData> = {
    /**
     * Get all entities with optional filtering
     */
    async getAll(
      search?: string,
      verified?: boolean,
      limit: number = 100,
      offset: number = 0
    ): Promise<TEntity[]> {
      const params = new URLSearchParams()

      if (search) {
        params.append('search', search)
      }

      if (verified !== undefined && verified !== null) {
        params.append('verified', verified.toString())
      }

      params.append('limit', limit.toString())
      params.append('offset', offset.toString())

      return await api.get<TEntity[]>(`/admin/${entityPath}?${params}`)
    },

    /**
     * Update an entity
     */
    async update(id: string, data: TUpdateData): Promise<TEntity> {
      return await api.put<TEntity>(`/admin/${entityPath}/${id}`, data)
    },

    /**
     * Merge source entity into target entity
     */
    async merge(sourceId: string, targetId: string): Promise<MergeResponse> {
      return await api.post<MergeResponse>(
        `/admin/${entityPath}/${sourceId}/merge/${targetId}`
      )
    },

    /**
     * Delete an entity
     */
    async delete(id: string): Promise<DeleteResponse> {
      return await api.delete<DeleteResponse>(`/admin/${entityPath}/${id}`)
    }
  }

  // Only add toggleVerification if entity supports it
  if (hasVerification) {
    api_methods.toggleVerification = async (id: string): Promise<TEntity> => {
      return await api.post<TEntity>(`/admin/${entityPath}/${id}/verify`)
    }
  }

  return api_methods
}
