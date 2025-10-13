import { api } from './client'
import { userSchema, type User } from '../schemas/user'

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
  login: (email: string, password: string) =>
    api.post<User>('/auth/login', { email, password }, userSchema),

  register: (name: string, email: string, password: string) =>
    api.post<User>('/auth/register', { name, email, password }, userSchema),

  logout: () =>
    api.post<void>('/auth/logout'),

  getCurrentUser: () =>
    api.get<User>('/auth/me', userSchema)
}
