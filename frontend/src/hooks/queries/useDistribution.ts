import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { distributionApi } from '../../api'
import type { DistributionSummary } from '../../schemas/distribution'
import { runKeys } from './useRuns'
import { createQueryKeys } from '../../utils/queryKeys'

// Query Keys
export const distributionKeys = createQueryKeys('distribution')

// ==================== Queries ====================

/**
 * Get distribution data for a run (grouped by distribution groups)
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
    onMutate: async (bidId: string) => {
      await queryClient.cancelQueries({ queryKey: distributionKeys.list(runId) })
      const previousData = queryClient.getQueryData(distributionKeys.list(runId))

      queryClient.setQueryData(distributionKeys.list(runId), (old: DistributionSummary | undefined) => {
        if (!old) return old
        return {
          ...old,
          groups: old.groups.map((group) => ({
            ...group,
            users: group.users.map((user) => ({
              ...user,
              products: user.products.map((product) =>
                product.bid_id === bidId
                  ? { ...product, is_picked_up: true }
                  : product
              ),
              all_picked_up: user.products.every((p) =>
                p.bid_id === bidId ? true : p.is_picked_up
              )
            }))
          }))
        }
      })

      return { previousData }
    },
    onError: (_err, _variables, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(distributionKeys.list(runId), context.previousData)
      }
    },
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
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      queryClient.invalidateQueries({ queryKey: distributionKeys.list(runId) })
    },
  })
}

/**
 * Create a new distribution group
 */
export function useCreateGroup(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => distributionApi.createGroup(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: distributionKeys.list(runId) })
    },
  })
}

/**
 * Delete a distribution group
 */
export function useDeleteGroup(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (groupId: string) => distributionApi.deleteGroup(runId, groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: distributionKeys.list(runId) })
    },
  })
}

/**
 * Assign a user to a distribution group
 */
export function useAssignUserToGroup(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, userId }: { groupId: string; userId: string }) =>
      distributionApi.assignUserToGroup(runId, groupId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: distributionKeys.list(runId) })
    },
  })
}

/**
 * Mark all items in a distribution group as picked up
 */
export function useMarkGroupDone(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (groupId: string) => distributionApi.markGroupDone(runId, groupId),
    onMutate: async (groupId: string) => {
      await queryClient.cancelQueries({ queryKey: distributionKeys.list(runId) })
      const previousData = queryClient.getQueryData(distributionKeys.list(runId))

      queryClient.setQueryData(distributionKeys.list(runId), (old: DistributionSummary | undefined) => {
        if (!old) return old
        return {
          ...old,
          groups: old.groups.map((group) =>
            group.id === groupId
              ? {
                  ...group,
                  is_done: true,
                  users: group.users.map((user) => ({
                    ...user,
                    products: user.products.map((p) => ({ ...p, is_picked_up: true })),
                    all_picked_up: true
                  }))
                }
              : group
          )
        }
      })

      return { previousData }
    },
    onError: (_err, _variables, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(distributionKeys.list(runId), context.previousData)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: distributionKeys.list(runId) })
    },
  })
}
