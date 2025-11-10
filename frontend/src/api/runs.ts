import { api } from './client'
import { runDetailSchema, type RunDetail } from '../schemas/run'
import { availableProductSchema } from '../schemas/product'
import { z } from 'zod'

export type { RunDetail }

export interface CreateRunRequest {
  group_id: string
  store_id: string
}

export interface PlaceBidRequest {
  product_id: string
  quantity: number
  interested_only: boolean
}

export const runsApi = {
  getRunDetails: (runId: string) =>
    api.get<RunDetail>(`/runs/${runId}`, runDetailSchema),

  createRun: (data: CreateRunRequest) =>
    api.post('/runs/create', data),

  placeBid: (runId: string, data: PlaceBidRequest) =>
    api.post(`/runs/${runId}/bids`, data),

  retractBid: (runId: string, productId: string) =>
    api.delete(`/runs/${runId}/bids/${productId}`),

  toggleReady: (runId: string) =>
    api.post(`/runs/${runId}/ready`),

  forceConfirm: (runId: string) =>
    api.post(`/runs/${runId}/force-confirm`),

  startShopping: (runId: string) =>
    api.post(`/runs/${runId}/start-shopping`),

  finishAdjusting: (runId: string, force: boolean = false) =>
    api.post(`/runs/${runId}/finish-adjusting?force=${force}`),

  cancelRun: (runId: string) =>
    api.post(`/runs/${runId}/cancel`),

  getAvailableProducts: (runId: string) =>
    api.get(`/runs/${runId}/available-products`, z.array(availableProductSchema)),

  toggleHelper: (runId: string, userId: string) =>
    api.post(`/runs/${runId}/helpers/${userId}`)
}
