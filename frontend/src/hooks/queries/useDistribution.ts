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
export function useDistribution(runId: string | undefined) {
  return useQuery({
    queryKey: distributionKeys.list(runId!),
    queryFn: () => distributionApi.getDistribution(runId!),
    enabled: !!runId,
  })
}

// ==================== Mutations ====================

/**
 * Mark a bid as picked up
 */
export function useMarkPickedUp(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (bidId: string) =>
      distributionApi.markPickedUp(runId, bidId),
    onSuccess: () => {
      // Invalidate distribution data to refetch
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
