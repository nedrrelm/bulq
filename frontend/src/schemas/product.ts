import { z } from 'zod'
import { uuidSchema, nullable, isoDateSchema } from './common'

/**
 * Product-related schemas
 */

export const productAvailabilitySchema = z.object({
  store_id: uuidSchema,
  store_name: z.string(),
  price: nullable(z.number())
})

// Note: productSearchResultSchema is same as productWithStoresSchema
// but kept for backward compatibility
export const productSearchResultSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  brand: nullable(z.string()),
  stores: z.array(productAvailabilitySchema)
})

// Available products from a run (simpler format)
export const availableProductSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  brand: nullable(z.string()),
  current_price: nullable(z.string())
})

// Product search result (includes stores array)
export const productWithStoresSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  brand: nullable(z.string()),
  stores: z.array(productAvailabilitySchema)
})

export const priceHistoryPointSchema = z.object({
  price: z.number(),
  notes: z.string(),
  timestamp: nullable(z.string())
})

export const storeWithPriceHistorySchema = z.object({
  store_id: uuidSchema,
  store_name: z.string(),
  current_price: nullable(z.number()),
  price_history: z.array(priceHistoryPointSchema),
  notes: z.string()
})

export const productDetailSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  brand: nullable(z.string()),
  unit: nullable(z.string()),
  stores: z.array(storeWithPriceHistorySchema)
})

export type ProductAvailability = z.infer<typeof productAvailabilitySchema>
export type ProductSearchResult = z.infer<typeof productSearchResultSchema>
export type AvailableProduct = z.infer<typeof availableProductSchema>
export type ProductDetail = z.infer<typeof productDetailSchema>
export type StoreWithPriceHistory = z.infer<typeof storeWithPriceHistorySchema>
