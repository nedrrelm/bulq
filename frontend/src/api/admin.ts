import { api } from './client'

export interface AdminUser {
  id: string
  name: string
  username: string
  verified: boolean
  is_admin: boolean
  created_at: string
}

export interface AdminProduct {
  id: string
  name: string
  brand: string | null
  unit: string | null
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

export interface MergeResponse {
  message: string
  source_id: string
  target_id: string
  affected_records: number
}

export interface DeleteResponse {
  message: string
  deleted_id: string
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

  async updateUser(userId: string, data: { name: string; username: string; is_admin: boolean; verified: boolean }): Promise<AdminUser> {
    return await api.put<AdminUser>(`/admin/users/${userId}`, data)
  },

  async deleteUser(userId: string): Promise<DeleteResponse> {
    return await api.delete<DeleteResponse>(`/admin/users/${userId}`)
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

  async updateProduct(productId: string, data: { name: string; brand?: string | null; unit?: string | null }): Promise<AdminProduct> {
    return await api.put<AdminProduct>(`/admin/products/${productId}`, data)
  },

  async mergeProducts(sourceId: string, targetId: string): Promise<MergeResponse> {
    return await api.post<MergeResponse>(`/admin/products/${sourceId}/merge/${targetId}`)
  },

  async deleteProduct(productId: string): Promise<DeleteResponse> {
    return await api.delete<DeleteResponse>(`/admin/products/${productId}`)
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

  async updateStore(storeId: string, data: { name: string; address?: string | null; chain?: string | null; opening_hours?: Record<string, string> | null }): Promise<AdminStore> {
    return await api.put<AdminStore>(`/admin/stores/${storeId}`, data)
  },

  async mergeStores(sourceId: string, targetId: string): Promise<MergeResponse> {
    return await api.post<MergeResponse>(`/admin/stores/${sourceId}/merge/${targetId}`)
  },

  async deleteStore(storeId: string): Promise<DeleteResponse> {
    return await api.delete<DeleteResponse>(`/admin/stores/${storeId}`)
  },

  async getRegistrationSetting(): Promise<{ allow_registration: boolean }> {
    return await api.get<{ allow_registration: boolean }>('/admin/settings/registration')
  },

  async setRegistrationSetting(allowRegistration: boolean): Promise<{ allow_registration: boolean; message: string }> {
    return await api.post<{ allow_registration: boolean; message: string }>(`/admin/settings/registration?allow_registration=${allowRegistration}`)
  },
}
