import { api } from './client'

export interface RunDetail {
  id: string
  group_id: string
  group_name: string
  store_id: string
  store_name: string
  state: string
  products: Array<{
    id: string
    name: string
    current_price: string | null
    total_quantity: number
    interested_count: number
    user_bids: Array<{
      user_id: string
      user_name: string
      quantity: number
      interested_only: boolean
    }>
    current_user_bid: {
      user_id: string
      user_name: string
      quantity: number
      interested_only: boolean
    } | null
    purchased_quantity: number | null
  }>
  participants: Array<{
    user_id: string
    user_name: string
    is_leader: boolean
    is_ready: boolean
    is_removed: boolean
  }>
  current_user_is_ready: boolean
  current_user_is_leader: boolean
}

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
    api.get<RunDetail>(`/runs/${runId}`),

  createRun: (data: CreateRunRequest) =>
    api.post('/runs/create', data),

  placeBid: (runId: string, data: PlaceBidRequest) =>
    api.post(`/runs/${runId}/bids`, data),

  retractBid: (runId: string, productId: string) =>
    api.delete(`/runs/${runId}/bids/${productId}`),

  toggleReady: (runId: string) =>
    api.post(`/runs/${runId}/ready`),

  startShopping: (runId: string) =>
    api.post(`/runs/${runId}/start-shopping`),

  finishAdjusting: (runId: string) =>
    api.post(`/runs/${runId}/finish-adjusting`),

  cancelRun: (runId: string) =>
    api.post(`/runs/${runId}/cancel`),

  getAvailableProducts: (runId: string) =>
    api.get(`/runs/${runId}/available-products`)
}
