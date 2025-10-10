import { z } from 'zod'
import { uuidSchema } from './common'

/**
 * Distribution-related schemas
 */

export const distributionParticipantSchema = z.object({
  user_id: uuidSchema,
  user_name: z.string(),
  quantity: z.number(),
  is_picked_up: z.boolean()
})

export const distributionItemSchema = z.object({
  product_id: uuidSchema,
  product_name: z.string(),
  participants: z.array(distributionParticipantSchema)
})

export type DistributionItem = z.infer<typeof distributionItemSchema>
export type DistributionParticipant = z.infer<typeof distributionParticipantSchema>
