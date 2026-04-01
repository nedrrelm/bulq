import { createContext } from 'react'
import type { User } from '../types/user'

export interface AuthContextType {
  user: User | null | undefined
  login: (userData: User) => void
  logout: () => Promise<void>
  updateUser: (userData: User) => void
  loading: boolean
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)
