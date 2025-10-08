import { api } from './client'

export interface Group {
  id: string
  name: string
  member_count: number
  active_runs_count: number
  completed_runs_count: number
  active_runs: Array<{
    id: string
    store_name: string
    state: string
  }>
}

export interface GroupDetails {
  id: string
  name: string
  invite_token: string
  members: Array<{
    id: string
    name: string
  }>
  runs: Array<{
    id: string
    store_name: string
    state: string
  }>
}

export interface CreateGroupRequest {
  name: string
}

export const groupsApi = {
  getMyGroups: () =>
    api.get<Group[]>('/groups/my-groups'),

  getGroup: (groupId: string) =>
    api.get<GroupDetails>(`/groups/${groupId}`),

  createGroup: (data: CreateGroupRequest) =>
    api.post<Group>('/groups/create', data),

  regenerateInvite: (groupId: string) =>
    api.post<{ invite_token: string }>(`/groups/${groupId}/regenerate-invite`),

  getGroupRuns: (groupId: string) =>
    api.get(`/groups/${groupId}/runs`),

  joinGroup: (inviteToken: string) =>
    api.post(`/groups/join/${inviteToken}`)
}
