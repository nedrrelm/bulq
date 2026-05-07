import { api } from './client'
import { z } from 'zod'
import { tagBriefSchema, type TagBrief } from '../schemas/product'

export type { TagBrief }

export interface TagSearchResult {
  id: string
  value: string
  type: string
  product_count: number
}

export interface TagDetail {
  id: string
  value: string
  type: string
  verified: boolean
  products: Array<{ id: string; name: string; brand: string | null; unit: string | null }>
  product_count: number
}

export interface CreateTagRequest {
  value: string
  type: string
}

export const tagsApi = {
  search: (query: string, type?: string) => {
    const params = new URLSearchParams({ q: query })
    if (type) params.append('type', type)
    return api.get<TagSearchResult[]>(`/tags/search?${params}`)
  },

  getTypes: () =>
    api.get<string[]>('/tags/types'),

  getTag: (tagId: string) =>
    api.get<TagDetail>(`/tags/${tagId}`),

  createTag: (data: CreateTagRequest) =>
    api.post('/tags/create', data),

  addTagToProduct: (tagId: string, productId: string) =>
    api.post(`/tags/${tagId}/products/${productId}`),

  removeTagFromProduct: (tagId: string, productId: string) =>
    api.delete(`/tags/${tagId}/products/${productId}`),

  getProductTags: (productId: string) =>
    api.get<TagBrief[]>(`/tags/product/${productId}`, z.array(tagBriefSchema)),
}
