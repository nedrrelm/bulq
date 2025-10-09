import { api } from './client'

export interface AdminUser {
  id: string
  name: string
  email: string
  verified: boolean
  is_admin: boolean
  created_at: string
}

export interface AdminProduct {
  id: string
  name: string
  brand: string | null
  store_name: string | null
  verified: boolean
  created_at: string
}

export interface AdminStore {
  id: string
  name: string
  address: string | null
  chain: string | null
  verified: boolean
  created_at: string
}

export const adminApi = {
  async getUsers(search?: string, verified?: boolean, limit: number = 100, offset: number = 0): Promise<AdminUser[]> {
    const params = new URLSearchParams()
    if (search) params.append('search', search)
    if (verified !== undefined && verified !== null) params.append('verified', verified.toString())
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())

    return await api.get<AdminUser[]>(`/admin/users?${params}`)
  },

  async toggleUserVerification(userId: string): Promise<AdminUser> {
    return await api.post<AdminUser>(`/admin/users/${userId}/verify`)
  },

  async getProducts(search?: string, verified?: boolean, limit: number = 100, offset: number = 0): Promise<AdminProduct[]> {
    const params = new URLSearchParams()
    if (search) params.append('search', search)
    if (verified !== undefined && verified !== null) params.append('verified', verified.toString())
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())

    return await api.get<AdminProduct[]>(`/admin/products?${params}`)
  },

  async toggleProductVerification(productId: string): Promise<AdminProduct> {
    return await api.post<AdminProduct>(`/admin/products/${productId}/verify`)
  },

  async getStores(search?: string, verified?: boolean, limit: number = 100, offset: number = 0): Promise<AdminStore[]> {
    const params = new URLSearchParams()
    if (search) params.append('search', search)
    if (verified !== undefined && verified !== null) params.append('verified', verified.toString())
    params.append('limit', limit.toString())
    params.append('offset', offset.toString())

    return await api.get<AdminStore[]>(`/admin/stores?${params}`)
  },

  async toggleStoreVerification(storeId: string): Promise<AdminStore> {
    return await api.post<AdminStore>(`/admin/stores/${storeId}/verify`)
  },
}
