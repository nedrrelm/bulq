import { z } from 'zod'
import { uuidSchema, nullable } from './common'

/**
 * Search-related schemas
 */

// Search products return the same format as ProductSearchResult
const searchProductStoreSchema = z.object({
  store_id: uuidSchema,
  store_name: z.string(),
  price: nullable(z.number())
})

export const searchProductSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  brand: nullable(z.string()),
  stores: z.array(searchProductStoreSchema)
})

export const searchStoreSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  address: nullable(z.string())
})

export const searchGroupSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  member_count: z.number()
})

export const searchResultsSchema = z.object({
  products: z.array(searchProductSchema).catch([]),
  stores: z.array(searchStoreSchema).catch([]),
  groups: z.array(searchGroupSchema).catch([])
}).transform(data => ({
  products: data.products ?? [],
  stores: data.stores ?? [],
  groups: data.groups ?? []
}))

export type SearchProduct = z.infer<typeof searchProductSchema>
export type SearchStore = z.infer<typeof searchStoreSchema>
export type SearchGroup = z.infer<typeof searchGroupSchema>
export type SearchResults = z.infer<typeof searchResultsSchema>
