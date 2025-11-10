import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { distributionApi } from '../../api'
import { runKeys } from './useRuns'

// Query Keys
export const distributionKeys = {
  all: ['distribution'] as const,
  lists: () => [...distributionKeys.all, 'list'] as const,
  list: (runId: string) => [...distributionKeys.lists(), runId] as const,
}

// ==================== Queries ====================

/**
 * Get distribution data for a run (user-centric view)
 */
export function useDistribution(runId: string | undefined, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: distributionKeys.list(runId!),
    queryFn: () => distributionApi.getDistribution(runId!),
    enabled: !!runId && (options?.enabled !== false),
  })
}

// ==================== Mutations ====================

/**
 * Mark a bid as picked up with optimistic updates
 */
export function useMarkPickedUp(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (bidId: string) =>
      distributionApi.markPickedUp(runId, bidId),
    // Optimistic update for instant feedback
    onMutate: async (bidId: string) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: distributionKeys.list(runId) })

      // Snapshot the previous value
      const previousData = queryClient.getQueryData(distributionKeys.list(runId))

      // Optimistically update
      queryClient.setQueryData(distributionKeys.list(runId), (old: any) => {
        if (!old) return old
        return old.map((user: any) => ({
          ...user,
          products: user.products.map((product: any) =>
            product.bid_id === bidId
              ? { ...product, is_picked_up: true }
              : product
          ),
          // Update all_picked_up flag
          all_picked_up: user.products.every((p: any) =>
            p.bid_id === bidId ? true : p.is_picked_up
          )
        }))
      })

      return { previousData }
    },
    // Rollback on error
    onError: (_err, _variables, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(distributionKeys.list(runId), context.previousData)
      }
    },
    // Always refetch after success or error
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: distributionKeys.list(runId) })
    },
  })
}

/**
 * Complete distribution (move run to completed state)
 */
export function useCompleteDistribution(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => distributionApi.completeDistribution(runId),
    onSuccess: () => {
      // Invalidate run details (state changed)
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      // Invalidate distribution data
      queryClient.invalidateQueries({ queryKey: distributionKeys.list(runId) })
    },
  })
}
