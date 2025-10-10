import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { runsApi } from '../../api'
import type { Run, ProductBid, RunParticipation, Product } from '../../types'
import { groupKeys } from './useGroups'

// Query Keys
export const runKeys = {
  all: ['runs'] as const,
  lists: () => [...runKeys.all, 'list'] as const,
  list: (filters?: any) => [...runKeys.lists(), filters] as const,
  details: () => [...runKeys.all, 'detail'] as const,
  detail: (id: string) => [...runKeys.details(), id] as const,
  participations: (id: string) => [...runKeys.detail(id), 'participations'] as const,
  bids: (id: string) => [...runKeys.detail(id), 'bids'] as const,
  availableProducts: (id: string) => [...runKeys.detail(id), 'available-products'] as const,
}

// ==================== Queries ====================

/**
 * Get a specific run's details
 */
export function useRun(runId: string | undefined) {
  return useQuery({
    queryKey: runKeys.detail(runId!),
    queryFn: () => runsApi.getRunDetails(runId!),
    enabled: !!runId,
  })
}

/**
 * Get participations for a run
 */
export function useRunParticipations(runId: string | undefined) {
  return useQuery({
    queryKey: runKeys.participations(runId!),
    queryFn: async () => {
      // The run details already include participations, so we can derive from there
      const run = await runsApi.getRunDetails(runId!)
      return run.participants || []
    },
    enabled: !!runId,
  })
}

/**
 * Get bids for a run
 */
export function useRunBids(runId: string | undefined) {
  return useQuery({
    queryKey: runKeys.bids(runId!),
    queryFn: async () => {
      // The run details already include bids, so we can derive from there
      const run = await runsApi.getRunDetails(runId!)
      return run.products || []
    },
    enabled: !!runId,
  })
}

/**
 * Get available products for a run
 */
export function useAvailableProducts(runId: string | undefined) {
  return useQuery({
    queryKey: runKeys.availableProducts(runId!),
    queryFn: () => runsApi.getAvailableProducts(runId!),
    enabled: !!runId,
  })
}

// ==================== Mutations ====================

/**
 * Create a new run
 */
export function useCreateRun(groupId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { store_id: string }) =>
      runsApi.createRun({ group_id: groupId, store_id: data.store_id }),
    onSuccess: () => {
      // Invalidate group's runs list
      queryClient.invalidateQueries({ queryKey: groupKeys.runs(groupId) })
    },
  })
}

/**
 * Cancel a run
 */
export function useCancelRun(runId: string, groupId?: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => runsApi.cancelRun(runId),
    onSuccess: () => {
      // Update run details
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      // Update group runs list if groupId provided
      if (groupId) {
        queryClient.invalidateQueries({ queryKey: groupKeys.runs(groupId) })
      }
    },
  })
}

/**
 * Place a bid on a product
 */
export function usePlaceBid(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { productId: string, quantity: number, interestedOnly: boolean }) =>
      runsApi.placeBid(runId, data.productId, data.quantity, data.interestedOnly),
    onSuccess: () => {
      // Invalidate run details to show new bid
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
    },
  })
}

/**
 * Update an existing bid
 */
export function useUpdateBid(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { productId: string, quantity: number, interestedOnly: boolean }) =>
      runsApi.updateBid(runId, data.productId, data.quantity, data.interestedOnly),
    onSuccess: () => {
      // Invalidate run details to show updated bid
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
    },
  })
}

/**
 * Retract a bid
 */
export function useRetractBid(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (productId: string) => runsApi.retractBid(runId, productId),
    onSuccess: () => {
      // Invalidate run details to remove bid
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
    },
  })
}

/**
 * Toggle ready status
 */
export function useToggleReady(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => runsApi.toggleReady(runId),
    // Optimistic update for instant feedback
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: runKeys.detail(runId) })

      // Snapshot the previous value
      const previousRun = queryClient.getQueryData<Run>(runKeys.detail(runId))

      // Optimistically update
      if (previousRun) {
        queryClient.setQueryData<Run>(runKeys.detail(runId), {
          ...previousRun,
          current_user_ready: !previousRun.current_user_ready,
        })
      }

      return { previousRun }
    },
    // Rollback on error
    onError: (_err, _variables, context) => {
      if (context?.previousRun) {
        queryClient.setQueryData(runKeys.detail(runId), context.previousRun)
      }
    },
    // Always refetch after success or error
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
    },
  })
}

/**
 * Confirm a run (move to confirmed state)
 */
export function useConfirmRun(runId: string, groupId?: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => runsApi.confirmRun(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
      if (groupId) {
        queryClient.invalidateQueries({ queryKey: groupKeys.runs(groupId) })
      }
    },
  })
}

/**
 * Start shopping (move to shopping state)
 */
export function useStartShopping(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => runsApi.startShopping(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
    },
  })
}

/**
 * Finish adjusting (after quantities adjusted)
 */
export function useFinishAdjusting(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => runsApi.finishAdjusting(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: runKeys.detail(runId) })
    },
  })
}

/**
 * Add a product to run's available products
 */
export function useAddProduct(runId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (productId: string) => runsApi.addProduct(runId, productId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: runKeys.availableProducts(runId) })
    },
  })
}
