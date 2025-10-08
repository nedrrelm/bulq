import { api } from './client'

export interface DistributionItem {
  product_id: string
  product_name: string
  participants: Array<{
    user_id: string
    user_name: string
    quantity: number
    is_picked_up: boolean
  }>
}

export interface TogglePickupRequest {
  user_id: string
  product_id: string
}

export const distributionApi = {
  getDistribution: (runId: string) =>
    api.get<DistributionItem[]>(`/distribution/${runId}`),

  togglePickup: (runId: string, data: TogglePickupRequest) =>
    api.post(`/distribution/${runId}/toggle-pickup`, data)
}
