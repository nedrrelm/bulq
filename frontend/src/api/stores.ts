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

  createStore: (request: CreateStoreRequest) =>
    api.post<Store>('/stores/create', request, storeSchema)
}
