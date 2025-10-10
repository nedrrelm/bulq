import { z } from 'zod'
import { uuidSchema, emailSchema } from './common'

/**
 * User schemas
 */

export const userSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  email: emailSchema,
  is_admin: z.boolean().optional()
})

export type User = z.infer<typeof userSchema>
