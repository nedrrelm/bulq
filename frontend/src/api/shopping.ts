import { api } from './client'
import { shoppingListItemSchema, type ShoppingListItem } from '../schemas/shopping'
import { z } from 'zod'

export type { ShoppingListItem }

export interface UpdateAvailabilityPriceRequest {
  price: number
  notes: string
  minimum_quantity?: number
}

export interface PurchaseRequest {
  quantity: number
  price_per_unit: number
  total: number
}

export interface AddMorePurchaseRequest {
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

  updatePurchase: (runId: string, itemId: string, data: PurchaseRequest) =>
    api.put(`/shopping/${runId}/items/${itemId}/purchase`, data),

  unpurchaseItem: (runId: string, itemId: string) =>
    api.delete(`/shopping/${runId}/items/${itemId}/purchase`),

  addProductToShoppingList: (runId: string, productId: string, quantity: number = 1.0) =>
    api.post(`/shopping/${runId}/items/${productId}`, { quantity }),

  addMorePurchase: (runId: string, itemId: string, data: AddMorePurchaseRequest) =>
    api.post(`/shopping/${runId}/items/${itemId}/add-more`, data),

  completeShopping: (runId: string) =>
    api.post(`/shopping/${runId}/complete`)
}
