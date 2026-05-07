import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sellersApi, type CreateSellerRequest, type UpdateSellerRequest } from '../../api/sellers'
import { createQueryKeys } from '../../utils/queryKeys'

// Query Keys
export const sellerKeys = createQueryKeys('sellers', {
  custom: {
    me: (base) => [...base, 'me'] as const,
    myFollowers: (base) => [...base, 'my-followers'] as const,
  },
  nested: {
    followedSellers: 'followed-sellers',
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

// ==================== Follower Queries ====================

/**
 * Get the current seller's followers
 */
export function useSellerFollowers() {
  return useQuery({
    queryKey: sellerKeys.myFollowers(),
    queryFn: () => sellersApi.getMyFollowers(),
  })
}

/**
 * Get which of the current user's groups follow a seller
 */
export function useMyFollowingGroups(sellerId: string | undefined) {
  return useQuery({
    queryKey: [...sellerKeys.detail(sellerId!), 'my-following'] as const,
    queryFn: () => sellersApi.getMyFollowingGroups(sellerId!),
    enabled: !!sellerId,
  })
}

/**
 * Get sellers followed by a group
 */
export function useFollowedSellers(groupId: string | undefined) {
  return useQuery({
    queryKey: sellerKeys.followedSellers(groupId!),
    queryFn: () => sellersApi.getFollowedSellers(groupId!),
    enabled: !!groupId,
  })
}

// ==================== Follower Mutations ====================

/**
 * Follow a seller with a group
 */
export function useFollowSeller() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sellerId, groupId }: { sellerId: string; groupId: string }) =>
      sellersApi.followSeller(sellerId, groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sellerKeys.myFollowers() })
      queryClient.invalidateQueries({ queryKey: sellerKeys.all })
    },
  })
}

/**
 * Unfollow a seller
 */
export function useUnfollowSeller() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ sellerId, groupId }: { sellerId: string; groupId: string }) =>
      sellersApi.unfollowSeller(sellerId, groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sellerKeys.myFollowers() })
      queryClient.invalidateQueries({ queryKey: sellerKeys.all })
    },
  })
}

/**
 * Follow a seller by invite token
 */
export function useFollowSellerByToken() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ inviteToken, groupId }: { inviteToken: string; groupId: string }) =>
      sellersApi.followByInviteToken(inviteToken, groupId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sellerKeys.all })
    },
  })
}
