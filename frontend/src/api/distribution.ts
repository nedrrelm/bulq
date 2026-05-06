import { api } from './client'
import { distributionSummarySchema, type DistributionUser, type DistributionProduct, type DistributionSummary, type DistributionGroup } from '../schemas/distribution'

export type { DistributionUser, DistributionProduct, DistributionSummary, DistributionGroup }

// For backwards compatibility with old code that may reference these names
export type DistributionItem = DistributionProduct
export interface TogglePickupRequest {
  bid_id: string
}

export const distributionApi = {
  /**
   * Get distribution data for a run (grouped by distribution groups)
   */
  getDistribution: (runId: string) =>
    api.get<DistributionSummary>(`/distribution/${runId}`, distributionSummarySchema),

  /**
   * Mark a specific bid as picked up
   */
  markPickedUp: (runId: string, bidId: string) =>
    api.post(`/distribution/${runId}/pickup/${bidId}`, {}),

  /**
   * Complete distribution and transition run to completed state
   */
  completeDistribution: (runId: string) =>
    api.post(`/distribution/${runId}/complete`, {}),

  /**
   * Create a new distribution group (auto-numbered)
   */
  createGroup: (runId: string) =>
    api.post(`/distribution/${runId}/groups`, {}),

  /**
   * Delete a distribution group (users moved to default group)
   */
  deleteGroup: (runId: string, groupId: string) =>
    api.delete(`/distribution/${runId}/groups/${groupId}`),

  /**
   * Assign a user to a distribution group
   */
  assignUserToGroup: (runId: string, groupId: string, userId: string) =>
    api.post(`/distribution/${runId}/groups/${groupId}/assign`, { user_id: userId }),

  /**
   * Mark all items in a distribution group as picked up
   */
  markGroupDone: (runId: string, groupId: string) =>
    api.post(`/distribution/${runId}/groups/${groupId}/done`, {})
}
