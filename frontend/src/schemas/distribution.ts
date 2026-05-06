import { z } from 'zod'
import { uuidSchema, nullable } from './common'

/**
 * Distribution-related schemas matching backend DistributionProduct and DistributionUser models
 */

export const distributionProductSchema = z.object({
  bid_id: uuidSchema,
  product_id: uuidSchema,
  product_name: z.string(),
  product_unit: nullable(z.string()),
  requested_quantity: z.number(),
  distributed_quantity: z.number(),
  price_per_unit: z.string(), // Decimal as string from backend
  subtotal: z.string(), // Decimal as string from backend
  is_picked_up: z.boolean()
})

export const distributionUserSchema = z.object({
  user_id: uuidSchema,
  user_name: z.string(),
  products: z.array(distributionProductSchema),
  total_cost: z.string(), // Decimal as string from backend
  fee_share: z.string().optional().default('0.00'),
  all_picked_up: z.boolean()
})

export const distributionGroupSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  is_default: z.boolean(),
  is_done: z.boolean(),
  sort_order: z.number(),
  users: z.array(distributionUserSchema),
  total_cost: z.string()
})

export const distributionSummarySchema = z.object({
  groups: z.array(distributionGroupSchema)
})

export type DistributionProduct = z.infer<typeof distributionProductSchema>
export type DistributionUser = z.infer<typeof distributionUserSchema>
export type DistributionGroup = z.infer<typeof distributionGroupSchema>
export type DistributionSummary = z.infer<typeof distributionSummarySchema>
