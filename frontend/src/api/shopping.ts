import { api } from './client'
import { shoppingListItemSchema, type ShoppingListItem } from '../schemas/shopping'
import { z } from 'zod'

export interface UpdateAvailabilityPriceRequest {
  price: number
  notes: string
}

export interface PurchaseRequest {
  quantity: number
  price_per_unit: number
  total: number
}

export const shoppingApi = {
  getShoppingList: (runId: string) =>
    api.get<ShoppingListItem[]>(`/shopping/${runId}/items`, z.array(shoppingListItemSchema)),

  updateAvailabilityPrice: (runId: string, itemId: string, data: UpdateAvailabilityPriceRequest) =>
    api.post(`/shopping/${runId}/items/${itemId}/price`, data),

  markPurchased: (runId: string, itemId: string, data: PurchaseRequest) =>
    api.post(`/shopping/${runId}/items/${itemId}/purchase`, data),

  completeShopping: (runId: string) =>
    api.post(`/shopping/${runId}/complete`)
}
