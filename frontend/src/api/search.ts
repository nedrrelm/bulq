import { api } from './client'
import { searchResultsSchema, type SearchResults, type SearchProduct, type SearchStore, type SearchGroup } from '../schemas/search'

export type { SearchResults, SearchProduct, SearchStore, SearchGroup }

export const searchApi = {
  searchAll: (query: string) =>
    api.get<SearchResults>(`/search?q=${encodeURIComponent(query)}`, searchResultsSchema)
}
