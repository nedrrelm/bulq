import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { shoppingApi } from '../../api'
import type { ShoppingListItem } from '../../types'
import { runKeys } from './useRuns'

// Query Keys
export const shoppingKeys = {
  all: ['shopping'] as const,
  lists: () => [...shoppingKeys.all, 'list'] as const,
  list: (runId: string) => [...shoppingKeys.lists(), runId] as const,
}

// ==================== Queries ====================

/**
 * Get shopping list for a run
 */
export function useShoppingList(runId: string | undefined) {
  return useQuery({
    queryKey: shoppingKeys.list(runId!),
    queryFn: () => shoppingApi.getShoppingList(runId!),
    enabled: !!runId,
  })
}

// ==================== Mutations ====================

/**
 * Mark an item as purchased
 */
export function useMarkPurchased(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: {
      itemId: string
      quantity: number
      pricePerUnit: number
      total: number
      purchaseOrder: number
    }) => shoppingApi.markItemPurchased(
      runId,
      data.itemId,
      data.quantity,
      data.pricePerUnit,
      data.total,
      data.purchaseOrder
    ),
    onSuccess: () => {
      // Invalidate shopping list
      queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
    },
  })
}

/**
 * Add encountered price for a product
 */
export function useAddEncounteredPrice(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { itemId: string, price: number, notes?: string }) =>
      shoppingApi.addEncounteredPrice(runId, data.itemId, data.price, data.notes),
    // No cache invalidation needed - this doesn't affect UI currently
  })
}

/**
 * Complete shopping (move run to next state)
 */
export function useCompleteShopping(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => shoppingApi.completeShopping(runId),
    onSuccess: () => {
      // Invalidate run details (state changed)
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      // Invalidate shopping list
      queryClient.invalidateQueries({ queryKey: shoppingKeys.list(runId) })
    },
  })
}
