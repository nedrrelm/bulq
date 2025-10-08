import { api } from './client'

export interface ProductSearchResult {
  id: string
  name: string
  store_name: string
  base_price: number | null
}

export interface ProductDetail {
  id: string
  name: string
  store_id: string
  store_name: string
  base_price: string
  price_history: Array<{
    price: string
    date: string
  }>
}

export interface CreateProductRequest {
  store_id: string
  name: string
  base_price: number
}

export const productsApi = {
  search: (query: string) =>
    api.get<ProductSearchResult[]>(`/products/search?q=${encodeURIComponent(query)}`),

  getProduct: (productId: string) =>
    api.get<ProductDetail>(`/products/${productId}`),

  createProduct: (data: CreateProductRequest) =>
    api.post('/products/create', data)
}
