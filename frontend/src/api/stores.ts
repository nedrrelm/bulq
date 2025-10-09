import { api } from './client'

export interface Store {
  id: string
  name: string
}

export interface CreateStoreRequest {
  name: string
}

export const storesApi = {
  getStores: () =>
    api.get<Store[]>('/stores'),

  createStore: (request: CreateStoreRequest) =>
    api.post<Store>('/stores/create', request)
}
