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
  requested_quantity: z.number().int(),
  distributed_quantity: z.number().int(),
  price_per_unit: z.string(), // Decimal as string from backend
  subtotal: z.string(), // Decimal as string from backend
  is_picked_up: z.boolean()
})

export const distributionUserSchema = z.object({
  user_id: uuidSchema,
  user_name: z.string(),
  products: z.array(distributionProductSchema),
  total_cost: z.string(), // Decimal as string from backend
  all_picked_up: z.boolean()
})

export type DistributionProduct = z.infer<typeof distributionProductSchema>
export type DistributionUser = z.infer<typeof distributionUserSchema>
