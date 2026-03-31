import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { storesApi } from '../../api'
import { createQueryKeys } from '../../utils/queryKeys'

// Query Keys
export const storeKeys = createQueryKeys('stores')

// ==================== Queries ====================

/**
 * Get all stores
 */
export function useStores() {
  return useQuery({
    queryKey: storeKeys.list(),
    queryFn: () => storesApi.getStores(),
    staleTime: 60000, // Stores don't change often, cache for 1 minute
  })
}

/**
 * Get a specific store's details
 */
export function useStore(storeId: string | undefined) {
  return useQuery({
    queryKey: storeKeys.detail(storeId!),
    queryFn: () => storesApi.getStores(),
    enabled: !!storeId,
    staleTime: 60000, // Stores don't change often
  })
}

// ==================== Mutations ====================

/**
 * Create a new store
 */
export function useCreateStore() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { name: string }) =>
      storesApi.createStore(data),
    onSuccess: () => {
      // Invalidate stores list
      queryClient.invalidateQueries({ queryKey: storeKeys.list() })
    },
  })
}
