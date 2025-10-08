import { api } from './client'

export interface Store {
  id: string
  name: string
}

export const storesApi = {
  getStores: () =>
    api.get<Store[]>('/stores')
}
