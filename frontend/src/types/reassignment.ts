export type ReassignmentStatus = 'pending' | 'accepted' | 'declined' | 'cancelled'

export interface LeaderReassignmentRequest {
  id: string
  run_id: string
  from_user_id: string
  from_user_name: string
  to_user_id: string
  to_user_name: string
  store_name: string
  status: ReassignmentStatus
  created_at: string
}

export interface PendingReassignments {
  sent: LeaderReassignmentRequest[]
  received: LeaderReassignmentRequest[]
}
