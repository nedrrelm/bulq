import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { groupsApi } from '../../api'
import type { Group, GroupDetails, GroupMember } from '../../types'

// Query Keys
export const groupKeys = {
  all: ['groups'] as const,
  lists: () => [...groupKeys.all, 'list'] as const,
  list: () => [...groupKeys.lists()] as const,
  details: () => [...groupKeys.all, 'detail'] as const,
  detail: (id: string) => [...groupKeys.details(), id] as const,
  runs: (id: string) => [...groupKeys.detail(id), 'runs'] as const,
  members: (id: string) => [...groupKeys.detail(id), 'members'] as const,
}

// ==================== Queries ====================

/**
 * Get all groups for the current user
 */
export function useGroups() {
  return useQuery({
    queryKey: groupKeys.list(),
    queryFn: () => groupsApi.getMyGroups(),
  })
}

/**
 * Get a specific group's details
 */
export function useGroup(groupId: string | undefined) {
  return useQuery({
    queryKey: groupKeys.detail(groupId!),
    queryFn: () => groupsApi.getGroup(groupId!),
    enabled: !!groupId,
  })
}

/**
 * Get a group by invite token
 */
export function useGroupByInvite(inviteToken: string | undefined) {
  return useQuery({
    queryKey: ['group', 'invite', inviteToken],
    queryFn: () => groupsApi.getGroup(inviteToken!),
    enabled: !!inviteToken,
    staleTime: 0, // Always fetch fresh for invite links
    cacheTime: 0, // Don't cache invite lookups
  })
}

/**
 * Get all runs for a group
 */
export function useGroupRuns(groupId: string | undefined) {
  return useQuery({
    queryKey: groupKeys.runs(groupId!),
    queryFn: () => groupsApi.getGroupRuns(groupId!),
    enabled: !!groupId,
  })
}

/**
 * Get all members of a group
 */
export function useGroupMembers(groupId: string | undefined) {
  return useQuery({
    queryKey: groupKeys.members(groupId!),
    queryFn: () => groupsApi.getGroupMembers(groupId!),
    enabled: !!groupId,
  })
}

// ==================== Mutations ====================

/**
 * Create a new group
 */
export function useCreateGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: { name: string }) => groupsApi.createGroup(data.name),
    onSuccess: () => {
      // Invalidate groups list to show new group
      queryClient.invalidateQueries({ queryKey: groupKeys.list() })
    },
  })
}

/**
 * Join a group via invite token
 */
export function useJoinGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (inviteToken: string) => groupsApi.joinGroup(inviteToken),
    onSuccess: () => {
      // Invalidate groups list to show joined group
      queryClient.invalidateQueries({ queryKey: groupKeys.list() })
    },
  })
}

/**
 * Leave a group
 */
export function useLeaveGroup(groupId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => groupsApi.leaveGroup(groupId),
    onSuccess: () => {
      // Remove from groups list
      queryClient.invalidateQueries({ queryKey: groupKeys.list() })
      // Remove group details cache
      queryClient.removeQueries({ queryKey: groupKeys.detail(groupId) })
    },
  })
}

/**
 * Regenerate group invite token
 */
export function useRegenerateInvite(groupId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => groupsApi.regenerateInvite(groupId),
    onSuccess: (data) => {
      // Update group details with new invite token
      queryClient.setQueryData<GroupDetails>(
        groupKeys.detail(groupId),
        (old) => old ? { ...old, invite_token: data.invite_token } : undefined
      )
    },
  })
}

/**
 * Remove a member from a group
 */
export function useRemoveMember(groupId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userId: string) => groupsApi.removeMember(groupId, userId),
    onSuccess: () => {
      // Refresh group members list
      queryClient.invalidateQueries({ queryKey: groupKeys.members(groupId) })
      // Refresh group details (member count may change)
      queryClient.invalidateQueries({ queryKey: groupKeys.detail(groupId) })
    },
  })
}
