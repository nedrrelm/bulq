import { api } from './client'
import type { User } from '../types/user'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
}

export const authApi = {
  login: (data: LoginRequest) =>
    api.post<User>('/auth/login', data),

  register: (data: RegisterRequest) =>
    api.post<User>('/auth/register', data),

  logout: () =>
    api.post<void>('/auth/logout'),

  getCurrentUser: () =>
    api.get<User>('/auth/me')
}
