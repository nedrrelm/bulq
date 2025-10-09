import { api } from './client'

export interface SearchProduct {
  id: string
  name: string
  store_id: string
  store_name: string
  base_price: number | null
}

export interface SearchStore {
  id: string
  name: string
  address: string | null
}

export interface SearchGroup {
  id: string
  name: string
  member_count: number
}

export interface SearchResults {
  products: SearchProduct[]
  stores: SearchStore[]
  groups: SearchGroup[]
}

export const searchApi = {
  searchAll: (query: string) =>
    api.get<SearchResults>(`/search?q=${encodeURIComponent(query)}`)
}
