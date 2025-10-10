import { api } from './client'

export interface ProductAvailability {
  store_id: string
  store_name: string
  price: number | null
}

export interface ProductSearchResult {
  id: string
  name: string
  brand: string | null
  stores: ProductAvailability[]
}

export interface StoreWithPriceHistory {
  store_id: string
  store_name: string
  current_price: number | null
  price_history: Array<{
    price: number
    notes: string
    timestamp: string | null
  }>
  notes: string
}

export interface ProductDetail {
  id: string
  name: string
  brand: string | null
  unit: string | null
  stores: StoreWithPriceHistory[]
}

export interface CreateProductRequest {
  name: string
  brand?: string | null
  unit?: string | null
  store_id?: string | null  // Optional: create availability if provided
  price?: number | null     // Optional: price for availability
}

export const productsApi = {
  search: (query: string) =>
    api.get<ProductSearchResult[]>(`/products/search?q=${encodeURIComponent(query)}`),

  getProduct: (productId: string) =>
    api.get<ProductDetail>(`/products/${productId}`),

  createProduct: (data: CreateProductRequest) =>
    api.post('/products/create', data)
}
