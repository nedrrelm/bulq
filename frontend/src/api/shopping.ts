import { api } from './client'

export interface ShoppingListItem {
  id: string
  product_id: string
  product_name: string
  requested_quantity: number
  encountered_prices: Array<{
    price: number
    notes: string
  }>
  purchased_quantity: number | null
  purchased_price_per_unit: string | null
  purchased_total: string | null
  is_purchased: boolean
  purchase_order: number | null
}

export interface EncounteredPriceRequest {
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
    api.get<ShoppingListItem[]>(`/shopping/${runId}/items`),

  addEncounteredPrice: (runId: string, itemId: string, data: EncounteredPriceRequest) =>
    api.post(`/shopping/${runId}/items/${itemId}/encountered-price`, data),

  markPurchased: (runId: string, itemId: string, data: PurchaseRequest) =>
    api.post(`/shopping/${runId}/items/${itemId}/purchase`, data),

  completeShopping: (runId: string) =>
    api.post(`/shopping/${runId}/complete`)
}
