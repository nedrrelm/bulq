import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productsApi } from '../../api'
import type { Product } from '../../types'

// Query Keys
export const productKeys = {
  all: ['products'] as const,
  lists: () => [...productKeys.all, 'list'] as const,
  list: (filters?: any) => [...productKeys.lists(), filters] as const,
  details: () => [...productKeys.all, 'detail'] as const,
  detail: (id: string) => [...productKeys.details(), id] as const,
  byStore: (storeId: string) => [...productKeys.lists(), { storeId }] as const,
}

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
export function useStoreProducts(storeId: string | undefined) {
  return useQuery({
    queryKey: productKeys.byStore(storeId!),
    queryFn: () => productsApi.getStoreProducts(storeId!),
    enabled: !!storeId,
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
      storeId: string
      name: string
      brand?: string
      unit?: string
      basePrice?: number
    }) => productsApi.createProduct(
      data.storeId,
      data.name,
      data.brand,
      data.unit,
      data.basePrice
    ),
    onSuccess: (newProduct) => {
      // Invalidate store products list
      queryClient.invalidateQueries({ queryKey: productKeys.byStore(newProduct.store_id) })
    },
  })
}
