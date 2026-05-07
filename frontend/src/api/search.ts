import { api } from './client'
import { searchResultsSchema, type SearchResults, type SearchProduct, type SearchStore, type SearchGroup, type SearchTag } from '../schemas/search'

export type { SearchResults, SearchProduct, SearchStore, SearchGroup, SearchTag }

export const searchApi = {
  searchAll: (query: string) =>
    api.get<SearchResults>(`/search?q=${encodeURIComponent(query)}`, searchResultsSchema)
}
