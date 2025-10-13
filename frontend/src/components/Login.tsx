import { useState, useEffect, useRef } from 'react'
import '../styles/components/Login.css'
import { authApi, ApiError } from '../api'
import type { User } from '../types/user'
import { sanitizeString } from '../utils/validation'

interface LoginProps {
  onLogin: (user: User) => void
}

interface LoginFormData {
  email: string
  password: string
}

interface RegisterFormData {
  name: string
  email: string
  password: string
}

export default function Login({ onLogin }: LoginProps) {
  const [isRegister, setIsRegister] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const emailInputRef = useRef<HTMLInputElement>(null)
  const nameInputRef = useRef<HTMLInputElement>(null)

  const [loginData, setLoginData] = useState<LoginFormData>({
    email: 'test@example.com',
    password: 'a'
  })

  const [registerData, setRegisterData] = useState<RegisterFormData>({
    name: '',
    email: '',
    password: ''
  })

  useEffect(() => {
    if (isRegister && nameInputRef.current) {
      nameInputRef.current.focus()
    } else if (!isRegister && emailInputRef.current) {
      emailInputRef.current.focus()
    }
  }, [isRegister])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const sanitizedEmail = sanitizeString(loginData.email.trim(), 255)
      const user = await authApi.login(sanitizedEmail, loginData.password)
      onLogin(user)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const sanitizedName = sanitizeString(registerData.name, 100)
      const sanitizedEmail = sanitizeString(registerData.email.trim(), 255)
      const user = await authApi.register(sanitizedName, sanitizedEmail, registerData.password)
      onLogin(user)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>{isRegister ? 'Create Account' : 'Sign In'}</h2>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {isRegister ? (
          <form onSubmit={handleRegister} className="auth-form">
            <div className="form-group">
              <label htmlFor="name" className="form-label">Name</label>
              <input
                type="text"
                id="name"
                className="form-input"
                value={registerData.name}
                onChange={(e) => setRegisterData({...registerData, name: e.target.value})}
                required
                disabled={loading}
                ref={nameInputRef}
              />
            </div>

            <div className="form-group">
              <label htmlFor="email" className="form-label">Email</label>
              <input
                type="email"
                id="email"
                className="form-input"
                value={registerData.email}
                onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                required
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <input
                type="password"
                id="password"
                className="form-input"
                value={registerData.password}
                onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                required
                disabled={loading}
                minLength={6}
              />
            </div>

            <button type="submit" disabled={loading} className="auth-button">
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleLogin} className="auth-form">
            <div className="form-group">
              <label htmlFor="email" className="form-label">Email</label>
              <input
                type="email"
                id="email"
                className="form-input"
                value={loginData.email}
                onChange={(e) => setLoginData({...loginData, email: e.target.value})}
                required
                disabled={loading}
                ref={emailInputRef}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <input
                type="password"
                id="password"
                className="form-input"
                value={loginData.password}
                onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                required
                disabled={loading}
              />
            </div>

            <button type="submit" disabled={loading} className="auth-button">
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>
        )}

        <div className="auth-switch">
          {isRegister ? (
            <p>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => setIsRegister(false)}
                className="link-button"
                disabled={loading}
              >
                Sign In
              </button>
            </p>
          ) : (
            <p>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => setIsRegister(true)}
                className="link-button"
                disabled={loading}
              >
                Create Account
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}