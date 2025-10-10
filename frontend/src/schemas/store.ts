import { z } from 'zod'
import { uuidSchema } from './common'

/**
 * Store schemas
 */

export const storeSchema = z.object({
  id: uuidSchema,
  name: z.string()
})

export type Store = z.infer<typeof storeSchema>
