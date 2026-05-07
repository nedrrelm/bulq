import { z } from 'zod'
import { uuidSchema } from './common'

/**
 * Seller schemas
 */

export const sellerSchema = z.object({
  id: uuidSchema,
  user_id: uuidSchema,
  store_id: uuidSchema,
  display_name: z.string(),
  description: z.string().nullable(),
  invite_token: z.string(),
  is_joining_allowed: z.boolean(),
  is_searchable: z.boolean(),
  created_at: z.string(),
})

export type Seller = z.infer<typeof sellerSchema>

export const sellerPublicSchema = z.object({
  id: uuidSchema,
  display_name: z.string(),
  description: z.string().nullable(),
  is_joining_allowed: z.boolean(),
})

export type SellerPublic = z.infer<typeof sellerPublicSchema>

export const sellerSearchResultSchema = z.object({
  id: uuidSchema,
  display_name: z.string(),
  description: z.string().nullable(),
})

export type SellerSearchResult = z.infer<typeof sellerSearchResultSchema>

export const sellerPreviewSchema = z.object({
  id: uuidSchema,
  display_name: z.string(),
  description: z.string().nullable(),
  is_joining_allowed: z.boolean(),
})

export type SellerPreview = z.infer<typeof sellerPreviewSchema>

// Follower schemas

export const sellerFollowerSchema = z.object({
  id: uuidSchema,
  seller_id: uuidSchema,
  group_id: uuidSchema,
  group_name: z.string(),
  member_count: z.number(),
  created_at: z.string(),
})

export type SellerFollower = z.infer<typeof sellerFollowerSchema>

export const followedSellerSchema = z.object({
  seller_id: uuidSchema,
  display_name: z.string(),
  description: z.string().nullable(),
  is_joining_allowed: z.boolean(),
})

export type FollowedSeller = z.infer<typeof followedSellerSchema>
