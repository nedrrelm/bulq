export interface StateDisplay {
  label: string
  color: string
  description: string
}

export function getStateLabel(state: string): string {
  switch (state) {
    case 'planning':
      return 'Planning'
    case 'active':
      return 'Active'
    case 'confirmed':
      return 'Confirmed'
    case 'shopping':
      return 'Shopping'
    case 'adjusting':
      return 'Adjusting'
    case 'distributing':
      return 'Distributing'
    case 'completed':
      return 'Completed'
    case 'cancelled':
      return 'Cancelled'
    default:
      return state
  }
}

export function getStateDisplay(state: string): StateDisplay {
  switch (state) {
    case 'planning':
      return { label: 'Planning', color: '#fbbf24', description: 'Collecting product interest' }
    case 'active':
      return { label: 'Active', color: '#10b981', description: 'Users placing bids and quantities' }
    case 'confirmed':
      return { label: 'Confirmed', color: '#3b82f6', description: 'Shopping list finalized' }
    case 'shopping':
      return { label: 'Shopping', color: '#8b5cf6', description: 'Designated shoppers executing the run' }
    case 'adjusting':
      return { label: 'Adjusting', color: '#f59e0b', description: 'Adjusting bids due to insufficient quantities' }
    case 'distributing':
      return { label: 'Distributing', color: '#14b8a6', description: 'Items being distributed to members' }
    case 'completed':
      return { label: 'Completed', color: '#6b7280', description: 'Run finished, costs calculated' }
    case 'cancelled':
      return { label: 'Cancelled', color: '#ef4444', description: 'Run was cancelled' }
    default:
      return { label: state, color: '#6b7280', description: '' }
  }
}
