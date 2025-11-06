import { z } from 'zod'
import { uuidSchema, nullable } from './common'

/**
 * Shopping-related schemas
 */

export const priceObservationSchema = z.object({
  price: z.number(),
  notes: z.string(),
  created_at: nullable(z.string())
})

export const shoppingListItemSchema = z.object({
  id: uuidSchema,
  product_id: uuidSchema,
  product_name: z.string(),
  product_unit: nullable(z.string()),
  requested_quantity: z.number(),
  recent_prices: z.array(priceObservationSchema),
  purchased_quantity: nullable(z.number()),
  purchased_price_per_unit: nullable(z.string()),
  purchased_total: nullable(z.string()),
  is_purchased: z.boolean(),
  purchase_order: nullable(z.number())
})

export type ShoppingListItem = z.infer<typeof shoppingListItemSchema>
export type PriceObservation = z.infer<typeof priceObservationSchema>
