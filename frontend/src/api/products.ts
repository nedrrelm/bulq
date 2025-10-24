import { api } from './client'
import {
  productSearchResultSchema,
  productDetailSchema,
  type ProductSearchResult,
  type ProductDetail
} from '../schemas/product'
import { z } from 'zod'

export type { ProductSearchResult, ProductDetail }

export interface CreateProductRequest {
  name: string
  brand?: string | null
  unit?: string | null
  store_id?: string | null  // Optional: create availability if provided
  price?: number | null     // Optional: price for availability
}

export const productsApi = {
  search: (query: string) =>
    api.get<ProductSearchResult[]>(`/products/search?q=${encodeURIComponent(query)}`, z.array(productSearchResultSchema)),

  checkSimilar: (name: string) =>
    api.get<ProductSearchResult[]>(`/products/check-similar?name=${encodeURIComponent(name)}`, z.array(productSearchResultSchema)),

  getProduct: (productId: string) =>
    api.get<ProductDetail>(`/products/${productId}`, productDetailSchema),

  createProduct: (data: CreateProductRequest) =>
    api.post('/products/create', data)
}
