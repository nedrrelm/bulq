import { api } from './client'
import type { LeaderReassignmentRequest, PendingReassignments } from '../types'

export const reassignmentApi = {
  async requestReassignment(runId: string, toUserId: string): Promise<LeaderReassignmentRequest> {
    return api.post('/reassignment/request', {
      run_id: runId,
      to_user_id: toUserId,
    })
  },

  async acceptReassignment(requestId: string): Promise<LeaderReassignmentRequest> {
    return api.post(`/reassignment/${requestId}/accept`)
  },

  async declineReassignment(requestId: string): Promise<LeaderReassignmentRequest> {
    return api.post(`/reassignment/${requestId}/decline`)
  },

  async cancelReassignment(requestId: string): Promise<LeaderReassignmentRequest> {
    return api.post(`/reassignment/${requestId}/cancel`)
  },

  async getMyRequests(): Promise<PendingReassignments> {
    return api.get('/reassignment/my-requests')
  },

  async getRunRequest(runId: string): Promise<{ request: LeaderReassignmentRequest | null }> {
    return api.get(`/reassignment/run/${runId}`)
  },
}
