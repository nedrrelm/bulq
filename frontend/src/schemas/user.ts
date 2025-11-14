import { z } from 'zod'
import { uuidSchema } from './common'

/**
 * User schemas
 */

export const userSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  username: z.string(),
  is_admin: z.boolean().optional(),
  dark_mode: z.boolean().optional(),
  preferred_language: z.string().optional().default('en')
})

export type User = z.infer<typeof userSchema>

export const userStatsSchema = z.object({
  total_quantity_bought: z.number(),
  total_money_spent: z.number(),
  runs_participated: z.number(),
  runs_helped: z.number(),
  runs_led: z.number(),
  groups_count: z.number()
})

export type UserStats = z.infer<typeof userStatsSchema>
