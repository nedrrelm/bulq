import { api } from './client'
import { searchResultsSchema, type SearchResults } from '../schemas/search'

export const searchApi = {
  searchAll: (query: string) =>
    api.get<SearchResults>(`/search?q=${encodeURIComponent(query)}`, searchResultsSchema)
}
