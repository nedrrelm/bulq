import { api } from './client'
import { z } from 'zod'
import {
  sellerSchema,
  sellerPublicSchema,
  sellerSearchResultSchema,
  sellerPreviewSchema,
  sellerFollowerSchema,
  followedSellerSchema,
  type Seller,
  type SellerPublic,
  type SellerSearchResult,
  type SellerPreview,
  type SellerFollower,
  type FollowedSeller,
} from '../schemas/seller'

export type { Seller, SellerPublic, SellerSearchResult, SellerPreview, SellerFollower, FollowedSeller }

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

  // Follower endpoints
  getMyFollowers: () =>
    api.get<SellerFollower[]>('/sellers/me/followers', z.array(sellerFollowerSchema)),

  getMyFollowingGroups: (sellerId: string) =>
    api.get<SellerFollower[]>(`/sellers/${sellerId}/my-following`, z.array(sellerFollowerSchema)),

  followSeller: (sellerId: string, groupId: string) =>
    api.post<SellerFollower>(`/sellers/${sellerId}/followers`, { group_id: groupId }, sellerFollowerSchema),

  unfollowSeller: (sellerId: string, groupId: string) =>
    api.delete(`/sellers/${sellerId}/followers/${groupId}`),

  followByInviteToken: (inviteToken: string, groupId: string) =>
    api.post<SellerFollower>(`/sellers/invite/${inviteToken}/follow`, { group_id: groupId }, sellerFollowerSchema),

  getFollowedSellers: (groupId: string) =>
    api.get<FollowedSeller[]>(`/groups/${groupId}/followed-sellers`, z.array(followedSellerSchema)),
}
