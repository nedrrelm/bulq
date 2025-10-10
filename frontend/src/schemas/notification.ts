import { z } from 'zod'
import { uuidSchema } from './common'

/**
 * Notification schemas
 */

export const notificationDataSchema = z.object({
  run_id: uuidSchema,
  store_name: z.string(),
  old_state: z.string(),
  new_state: z.string(),
  group_id: uuidSchema
})

export const notificationSchema = z.object({
  id: uuidSchema,
  type: z.string(),
  data: notificationDataSchema,
  read: z.boolean(),
  created_at: z.string(),
  grouped: z.boolean().optional(),
  count: z.number().optional(),
  notification_ids: z.array(uuidSchema).optional()
})

export type Notification = z.infer<typeof notificationSchema>
export type NotificationData = z.infer<typeof notificationDataSchema>
