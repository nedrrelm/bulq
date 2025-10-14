import { useQuery } from '@tanstack/react-query'
import { searchApi } from '../../api'

// Query Keys
export const searchKeys = {
  all: ['search'] as const,
  results: (query: string) => [...searchKeys.all, query] as const,
}

// ==================== Queries ====================

/**
 * Global search across stores and products
 */
export function useSearch(query: string | undefined) {
  return useQuery({
    queryKey: searchKeys.results(query || ''),
    queryFn: () => searchApi.searchAll(query!),
    enabled: !!query && query.length >= 2, // Only search with 2+ characters
    staleTime: 30000, // Search results stay fresh for 30 seconds
  })
}
