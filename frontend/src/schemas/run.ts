import { z } from 'zod'
import { uuidSchema, nullable } from './common'

/**
 * Run-related schemas
 */

export const userBidSchema = z.object({
  user_id: uuidSchema,
  user_name: z.string(),
  quantity: z.number(),
  interested_only: z.boolean()
})

export const productInRunSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  brand: nullable(z.string()),
  unit: nullable(z.string()),
  current_price: nullable(z.string()),
  total_quantity: z.number(),
  interested_count: z.number(),
  user_bids: z.array(userBidSchema),
  current_user_bid: nullable(userBidSchema),
  purchased_quantity: nullable(z.number())
})

export const participantSchema = z.object({
  user_id: uuidSchema,
  user_name: z.string(),
  is_leader: z.boolean(),
  is_helper: z.boolean(),
  is_ready: z.boolean(),
  is_removed: z.boolean().optional().default(false)
})

export const runDetailSchema = z.object({
  id: uuidSchema,
  group_id: uuidSchema,
  group_name: z.string(),
  store_id: uuidSchema,
  store_name: z.string(),
  state: z.string(),
  comment: nullable(z.string()),
  products: z.array(productInRunSchema),
  participants: z.array(participantSchema),
  current_user_is_ready: z.boolean(),
  current_user_is_leader: z.boolean(),
  current_user_is_helper: z.boolean(),
  leader_name: z.string(),
  helpers: z.array(z.string())
})

export type RunDetail = z.infer<typeof runDetailSchema>
export type Run = RunDetail
export type ProductInRun = z.infer<typeof productInRunSchema>
export type Participant = z.infer<typeof participantSchema>
export type UserBid = z.infer<typeof userBidSchema>
