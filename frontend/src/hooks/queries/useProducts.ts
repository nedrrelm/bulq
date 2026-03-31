import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productsApi } from '../../api'
import { createQueryKeys } from '../../utils/queryKeys'

// Query Keys
export const productKeys = createQueryKeys('products', {
  filters: {
    byStore: (storeId: string) => ({ storeId })
  }
})

// ==================== Queries ====================

/**
 * Get a specific product's details
 */
export function useProduct(productId: string | undefined) {
  return useQuery({
    queryKey: productKeys.detail(productId!),
    queryFn: () => productsApi.getProduct(productId!),
    enabled: !!productId,
  })
}

/**
 * Get products for a store
 */
export function useStoreProducts(_storeId: string | undefined) {
  return useQuery({
    queryKey: productKeys.byStore(_storeId!),
    queryFn: () => productsApi.search(''),
    enabled: !!_storeId,
  })
}

// ==================== Mutations ====================

/**
 * Create a new product
 */
export function useCreateProduct() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      name: string
      brand?: string | null
      unit?: string | null
      store_id?: string | null
      price?: number | null
    }) => productsApi.createProduct(data),
    onSuccess: () => {
      // Invalidate products list
      queryClient.invalidateQueries({ queryKey: productKeys.lists() })
    },
  })
}
