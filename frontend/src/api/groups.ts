import { api } from './client'
import { z } from 'zod'
import {
  groupSchema,
  groupBasicInfoSchema,
  groupManageDetailsSchema,
  type Group,
  type GroupBasicInfo,
  type GroupManageDetails
} from '../schemas/group'

export interface CreateGroupRequest {
  name: string
}

const regenerateInviteResponseSchema = z.object({
  invite_token: z.string()
})

const toggleJoiningResponseSchema = z.object({
  is_joining_allowed: z.boolean()
})

export const groupsApi = {
  getMyGroups: () =>
    api.get<Group[]>('/groups/my-groups', z.array(groupSchema)),

  getGroup: (groupId: string) =>
    api.get<GroupBasicInfo>(`/groups/${groupId}`, groupBasicInfoSchema),

  createGroup: (data: CreateGroupRequest) =>
    api.post<Group>('/groups/create', data, groupSchema),

  regenerateInvite: (groupId: string) =>
    api.post<{ invite_token: string }>(`/groups/${groupId}/regenerate-invite`, undefined, regenerateInviteResponseSchema),

  getGroupRuns: (groupId: string) =>
    api.get(`/groups/${groupId}/runs`),

  joinGroup: (inviteToken: string) =>
    api.post(`/groups/join/${inviteToken}`),

  getGroupMembers: (groupId: string) =>
    api.get<GroupManageDetails>(`/groups/${groupId}/members`, groupManageDetailsSchema),

  removeMember: (groupId: string, memberId: string) =>
    api.delete(`/groups/${groupId}/members/${memberId}`),

  toggleJoiningAllowed: (groupId: string) =>
    api.post<{ is_joining_allowed: boolean }>(`/groups/${groupId}/toggle-joining`, undefined, toggleJoiningResponseSchema),

  leaveGroup: (groupId: string) =>
    api.post(`/groups/${groupId}/leave`),

  promoteMemberToAdmin: (groupId: string, memberId: string) =>
    api.post(`/groups/${groupId}/members/${memberId}/promote`)
}
