import { z } from 'zod'
import { uuidSchema, nullable } from './common'

export const saleProductSchema = z.object({
  id: uuidSchema,
  product_id: uuidSchema,
  product_name: z.string(),
  product_brand: nullable(z.string()),
  product_unit: nullable(z.string()),
  price: nullable(z.string()),
  available_quantity: nullable(z.string()),
})

export type SaleProduct = z.infer<typeof saleProductSchema>

export const saleSchema = z.object({
  id: uuidSchema,
  seller_id: uuidSchema,
  seller_name: nullable(z.string()).optional(),
  title: z.string(),
  description: nullable(z.string()),
  state: z.string(),
  product_count: z.number(),
  created_at: z.string(),
})

export type Sale = z.infer<typeof saleSchema>

export const saleDetailSchema = z.object({
  id: uuidSchema,
  seller_id: uuidSchema,
  seller_name: z.string(),
  title: z.string(),
  description: nullable(z.string()),
  state: z.string(),
  invite_token: z.string(),
  products: z.array(saleProductSchema),
  planning_at: nullable(z.string()),
  active_at: nullable(z.string()),
  confirmed_at: nullable(z.string()),
  shopping_at: nullable(z.string()),
  distributing_at: nullable(z.string()),
  completed_at: nullable(z.string()),
  cancelled_at: nullable(z.string()),
  created_at: z.string(),
})

export type SaleDetail = z.infer<typeof saleDetailSchema>
