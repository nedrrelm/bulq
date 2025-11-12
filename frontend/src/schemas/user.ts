import { z } from 'zod'
import { uuidSchema } from './common'

/**
 * User schemas
 */

export const userSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  username: z.string(),
  is_admin: z.boolean().optional()
})

export type User = z.infer<typeof userSchema>
