export interface Notification {
  id: string
  type: string
  data: NotificationData
  read: boolean
  created_at: string
  grouped?: boolean
  count?: number
  notification_ids?: string[]
}

export interface NotificationData {
  run_id: string
  store_name: string
  old_state: string
  new_state: string
  group_id: string
}
