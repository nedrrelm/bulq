import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sellersApi, type CreateSellerRequest, type UpdateSellerRequest } from '../../api/sellers'
import { createQueryKeys } from '../../utils/queryKeys'

// Query Keys
export const sellerKeys = createQueryKeys('sellers', {
  custom: {
    me: (base) => [...base, 'me'] as const,
  },
})

// ==================== Queries ====================

/**
 * Get the current user's seller profile (or null)
 */
export function useMySellerProfile() {
  return useQuery({
    queryKey: sellerKeys.me(),
    queryFn: () => sellersApi.getMyProfile(),
  })
}

/**
 * Get a seller's public profile
 */
export function useSeller(sellerId: string | undefined) {
  return useQuery({
    queryKey: sellerKeys.detail(sellerId!),
    queryFn: () => sellersApi.getSeller(sellerId!),
    enabled: !!sellerId,
  })
}

/**
 * Search sellers by name
 */
export function useSellerSearch(query: string) {
  return useQuery({
    queryKey: sellerKeys.list({ search: query }),
    queryFn: () => sellersApi.searchSellers(query),
    enabled: query.length >= 2,
  })
}

// ==================== Mutations ====================

/**
 * Create a seller profile
 */
export function useCreateSeller() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateSellerRequest) =>
      sellersApi.createSeller(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sellerKeys.me() })
    },
  })
}

/**
 * Update seller profile
 */
export function useUpdateSeller() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: UpdateSellerRequest) =>
      sellersApi.updateMyProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sellerKeys.me() })
    },
  })
}

/**
 * Toggle joining allowed
 */
export function useToggleJoiningAllowed() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => sellersApi.toggleJoiningAllowed(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sellerKeys.me() })
    },
  })
}

/**
 * Toggle searchable
 */
export function useToggleSearchable() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => sellersApi.toggleSearchable(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sellerKeys.me() })
    },
  })
}

/**
 * Regenerate invite token
 */
export function useRegenerateSellerToken() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => sellersApi.regenerateInviteToken(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sellerKeys.me() })
    },
  })
}
