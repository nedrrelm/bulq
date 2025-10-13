/**
 * WebSocket message types for type-safe WebSocket communication
 */

// Base WebSocket message structure
export interface WebSocketMessage<T = unknown> {
  type: string
  data: T
  timestamp?: string
}

// Run-related WebSocket messages
export interface BidUpdatedData {
  run_id: string
  product_id: string
  user_id: string
  user_name: string
  quantity: number
  interested_only: boolean
}

export interface RunStateChangedData {
  run_id: string
  group_id?: string
  new_state: string
  old_state: string
}

export interface RunCreatedData {
  run_id: string
  group_id: string
  store_name: string
}

export interface ParticipantReadyData {
  run_id: string
  user_id: string
  user_name: string
  is_ready: boolean
}

// Group-related WebSocket messages
export interface MemberRemovedData {
  group_id: string
  removed_user_id: string
  removed_user_name: string
  removed_by_id: string
  removed_by_name: string
}

export interface MemberLeftData {
  group_id: string
  user_id: string
  user_name: string
}

// Leader reassignment WebSocket messages
export interface LeaderReassignmentRequestedData {
  run_id: string
  from_user_id: string
  from_user_name: string
  to_user_id: string
  to_user_name: string
}

export interface LeaderReassignmentAcceptedData {
  run_id: string
  new_leader_id: string
  new_leader_name: string
  old_leader_id: string
  old_leader_name: string
}

export interface LeaderReassignmentRejectedData {
  run_id: string
  from_user_id: string
  from_user_name: string
  to_user_id: string
  to_user_name: string
}

// Union type for all WebSocket message data types
export type WebSocketMessageData =
  | BidUpdatedData
  | RunStateChangedData
  | RunCreatedData
  | ParticipantReadyData
  | MemberRemovedData
  | MemberLeftData
  | LeaderReassignmentRequestedData
  | LeaderReassignmentAcceptedData
  | LeaderReassignmentRejectedData

// Typed WebSocket messages
export type BidUpdatedMessage = WebSocketMessage<BidUpdatedData>
export type RunStateChangedMessage = WebSocketMessage<RunStateChangedData>
export type RunCreatedMessage = WebSocketMessage<RunCreatedData>
export type ParticipantReadyMessage = WebSocketMessage<ParticipantReadyData>
export type MemberRemovedMessage = WebSocketMessage<MemberRemovedData>
export type MemberLeftMessage = WebSocketMessage<MemberLeftData>
export type LeaderReassignmentRequestedMessage = WebSocketMessage<LeaderReassignmentRequestedData>
export type LeaderReassignmentAcceptedMessage = WebSocketMessage<LeaderReassignmentAcceptedData>
export type LeaderReassignmentRejectedMessage = WebSocketMessage<LeaderReassignmentRejectedData>

// Union type for all possible WebSocket messages
export type AnyWebSocketMessage =
  | BidUpdatedMessage
  | RunStateChangedMessage
  | RunCreatedMessage
  | ParticipantReadyMessage
  | MemberRemovedMessage
  | MemberLeftMessage
  | LeaderReassignmentRequestedMessage
  | LeaderReassignmentAcceptedMessage
  | LeaderReassignmentRejectedMessage

// Type guard functions for runtime type checking
export function isBidUpdatedMessage(msg: WebSocketMessage): msg is BidUpdatedMessage {
  return msg.type === 'bid_updated'
}

export function isRunStateChangedMessage(msg: WebSocketMessage): msg is RunStateChangedMessage {
  return msg.type === 'run_state_changed'
}

export function isRunCreatedMessage(msg: WebSocketMessage): msg is RunCreatedMessage {
  return msg.type === 'run_created'
}

export function isParticipantReadyMessage(msg: WebSocketMessage): msg is ParticipantReadyMessage {
  return msg.type === 'participant_ready'
}

export function isMemberRemovedMessage(msg: WebSocketMessage): msg is MemberRemovedMessage {
  return msg.type === 'member_removed'
}

export function isMemberLeftMessage(msg: WebSocketMessage): msg is MemberLeftMessage {
  return msg.type === 'member_left'
}

export function isLeaderReassignmentRequestedMessage(msg: WebSocketMessage): msg is LeaderReassignmentRequestedMessage {
  return msg.type === 'leader_reassignment_requested'
}

export function isLeaderReassignmentAcceptedMessage(msg: WebSocketMessage): msg is LeaderReassignmentAcceptedMessage {
  return msg.type === 'leader_reassignment_accepted'
}

export function isLeaderReassignmentRejectedMessage(msg: WebSocketMessage): msg is LeaderReassignmentRejectedMessage {
  return msg.type === 'leader_reassignment_rejected'
}
