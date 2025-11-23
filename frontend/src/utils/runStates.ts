import i18n from '../i18n/config'

export interface StateDisplay {
  label: string
  color: string
  description: string
}

export function getStateLabel(state: string): string {
  const key = `run:states.${state}`
  if (i18n.exists(key)) {
    return i18n.t(key)
  }
  return state
}

export function getStateDisplay(state: string): StateDisplay {
  const label = getStateLabel(state)
  const descriptionKey = `run:states.${state}Description`
  const description = i18n.exists(descriptionKey) ? i18n.t(descriptionKey) : ''

  switch (state) {
    case 'planning':
      return { label, color: '#fbbf24', description }
    case 'active':
      return { label, color: '#10b981', description }
    case 'confirmed':
      return { label, color: '#3b82f6', description }
    case 'shopping':
      return { label, color: '#8b5cf6', description }
    case 'adjusting':
      return { label, color: '#f59e0b', description }
    case 'distributing':
      return { label, color: '#14b8a6', description }
    case 'completed':
      return { label, color: '#6b7280', description }
    case 'cancelled':
      return { label, color: '#ef4444', description }
    default:
      return { label, color: '#6b7280', description }
  }
}
