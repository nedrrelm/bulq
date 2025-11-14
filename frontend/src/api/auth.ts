import { api } from './client'
import { userSchema, userStatsSchema, type User, type UserStats } from '../schemas/user'

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
    api.get<User>('/auth/me', userSchema),

  getProfileStats: () =>
    api.get<UserStats>('/auth/profile/stats', userStatsSchema),

  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<void>('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    }),

  changeUsername: (currentPassword: string, newUsername: string) =>
    api.post<User>('/auth/change-username', {
      current_password: currentPassword,
      new_username: newUsername
    }, userSchema),

  changeName: (currentPassword: string, newName: string) =>
    api.post<User>('/auth/change-name', {
      current_password: currentPassword,
      new_name: newName
    }, userSchema),

  toggleDarkMode: () =>
    api.post<User>('/auth/toggle-dark-mode', {}, userSchema),

  changeLanguage: (language: string) =>
    api.post<User>('/auth/change-language', { language }, userSchema)
}
