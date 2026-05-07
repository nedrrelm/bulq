import { api } from './client'
import { z } from 'zod'
import {
  sellerSchema,
  sellerPublicSchema,
  sellerSearchResultSchema,
  sellerPreviewSchema,
  type Seller,
  type SellerPublic,
  type SellerSearchResult,
  type SellerPreview,
} from '../schemas/seller'

export type { Seller, SellerPublic, SellerSearchResult, SellerPreview }

export interface CreateSellerRequest {
  display_name: string
  description?: string | null
}

export interface UpdateSellerRequest {
  display_name?: string | null
  description?: string | null
}

// Nullable seller schema for GET /me (returns null if no profile)
const nullableSellerSchema = sellerSchema.nullable()

export const sellersApi = {
  createSeller: (request: CreateSellerRequest) =>
    api.post<Seller>('/sellers', request, sellerSchema),

  getMyProfile: () =>
    api.get<Seller | null>('/sellers/me', nullableSellerSchema),

  updateMyProfile: (request: UpdateSellerRequest) =>
    api.patch<Seller>('/sellers/me', request, sellerSchema),

  toggleJoiningAllowed: () =>
    api.patch<Seller>('/sellers/me/joining', {}, sellerSchema),

  toggleSearchable: () =>
    api.patch<Seller>('/sellers/me/searchable', {}, sellerSchema),

  regenerateInviteToken: () =>
    api.post<Seller>('/sellers/me/regenerate-token', {}, sellerSchema),

  searchSellers: (query: string) =>
    api.get<SellerSearchResult[]>(
      `/sellers/search?q=${encodeURIComponent(query)}`,
      z.array(sellerSearchResultSchema)
    ),

  getSellerByInviteToken: (token: string) =>
    api.get<SellerPreview>(`/sellers/invite/${token}`, sellerPreviewSchema),

  getSeller: (sellerId: string) =>
    api.get<SellerPublic>(`/sellers/${sellerId}`, sellerPublicSchema),
}
