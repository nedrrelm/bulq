import { api } from './client'
import { distributionItemSchema, type DistributionItem } from '../schemas/distribution'
import { z } from 'zod'

export interface TogglePickupRequest {
  user_id: string
  product_id: string
}

export const distributionApi = {
  getDistribution: (runId: string) =>
    api.get<DistributionItem[]>(`/distribution/${runId}`, z.array(distributionItemSchema)),

  togglePickup: (runId: string, data: TogglePickupRequest) =>
    api.post(`/distribution/${runId}/toggle-pickup`, data)
}
