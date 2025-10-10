import { z } from 'zod'
import { uuidSchema, nullable, emailSchema } from './common'

/**
 * Group-related schemas
 */

export const activeRunSummarySchema = z.object({
  id: uuidSchema,
  store_name: z.string(),
  state: z.string()
})

export const groupSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  member_count: z.number(),
  active_runs_count: z.number(),
  completed_runs_count: z.number(),
  active_runs: z.array(activeRunSummarySchema)
})

export const runSummarySchema = z.object({
  id: uuidSchema,
  group_id: uuidSchema,
  store_id: uuidSchema,
  store_name: z.string(),
  state: z.string(),
  leader_name: z.string(),
  leader_is_removed: z.boolean(),
  planned_on: nullable(z.string())
})

export const groupMemberBasicSchema = z.object({
  id: uuidSchema,
  name: z.string()
})

// Basic group info (just id, name, invite_token)
export const groupBasicInfoSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  invite_token: z.string()
})

// Full group details (includes members and runs)
export const groupDetailsSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  invite_token: z.string(),
  members: z.array(groupMemberBasicSchema),
  runs: z.array(runSummarySchema)
})

export const groupMemberSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  email: emailSchema,
  is_group_admin: z.boolean()
})

export const groupManageDetailsSchema = z.object({
  id: uuidSchema,
  name: z.string(),
  invite_token: z.string(),
  is_joining_allowed: z.boolean(),
  members: z.array(groupMemberSchema),
  is_current_user_admin: z.boolean()
})

export type Group = z.infer<typeof groupSchema>
export type GroupBasicInfo = z.infer<typeof groupBasicInfoSchema>
export type GroupDetails = z.infer<typeof groupDetailsSchema>
export type GroupMember = z.infer<typeof groupMemberSchema>
export type GroupManageDetails = z.infer<typeof groupManageDetailsSchema>
