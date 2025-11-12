import { api } from './client'
import { userSchema, type User } from '../schemas/user'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  name: string
  username: string
  password: string
}

export const authApi = {
  login: (username: string, password: string) =>
    api.post<User>('/auth/login', { username, password }, userSchema),

  register: (name: string, username: string, password: string) =>
    api.post<User>('/auth/register', { name, username, password }, userSchema),

  logout: () =>
    api.post<void>('/auth/logout'),

  getCurrentUser: () =>
    api.get<User>('/auth/me', userSchema)
}
