import { api } from './client'
import { distributionUserSchema, type DistributionUser } from '../schemas/distribution'
import { z } from 'zod'

export const distributionApi = {
  /**
   * Get distribution data for a run (user-centric view)
   */
  getDistribution: (runId: string) =>
    api.get<DistributionUser[]>(`/distribution/${runId}`, z.array(distributionUserSchema)),

  /**
   * Mark a specific bid as picked up
   */
  markPickedUp: (runId: string, bidId: string) =>
    api.post(`/distribution/${runId}/pickup/${bidId}`, {}),

  /**
   * Complete distribution and transition run to completed state
   */
  completeDistribution: (runId: string) =>
    api.post(`/distribution/${runId}/complete`, {})
}
