import { api } from './client'
import { storeSchema, type Store } from '../schemas/store'
import { z } from 'zod'

export type { Store }

export interface CreateStoreRequest {
  name: string
}

export const storesApi = {
  getStores: () =>
    api.get<Store[]>('/stores', z.array(storeSchema)),

  checkSimilar: (name: string) =>
    api.get<Store[]>(`/stores/check-similar?name=${encodeURIComponent(name)}`, z.array(storeSchema)),

  createStore: (request: CreateStoreRequest) =>
    api.post<Store>('/stores/create', request, storeSchema)
}
