import { useState, useEffect, useRef } from 'react'
import '../styles/components/Login.css'
import { authApi, ApiError } from '../api'
import type { User } from '../types/user'
import { sanitizeString } from '../utils/validation'

interface LoginProps {
  onLogin: (user: User) => void
}

interface LoginFormData {
  username: string
  password: string
}

interface RegisterFormData {
  name: string
  username: string
  password: string
  confirmPassword: string
}

export default function Login({ onLogin }: LoginProps) {
  const [isRegister, setIsRegister] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const usernameInputRef = useRef<HTMLInputElement>(null)
  const nameInputRef = useRef<HTMLInputElement>(null)

  const [loginData, setLoginData] = useState<LoginFormData>({
    username: '',
    password: ''
  })

  const [registerData, setRegisterData] = useState<RegisterFormData>({
    name: '',
    username: '',
    password: '',
    confirmPassword: ''
  })

  useEffect(() => {
    if (isRegister && nameInputRef.current) {
      nameInputRef.current.focus()
    } else if (!isRegister && usernameInputRef.current) {
      usernameInputRef.current.focus()
    }
  }, [isRegister])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const sanitizedUsername = sanitizeString(loginData.username.trim(), 50)
      const user = await authApi.login(sanitizedUsername, loginData.password)
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

    // Validate password confirmation
    if (registerData.password !== registerData.confirmPassword) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      const sanitizedName = sanitizeString(registerData.name, 100)
      const sanitizedUsername = sanitizeString(registerData.username.trim(), 50)
      const user = await authApi.register(sanitizedName, sanitizedUsername, registerData.password)
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
              <label htmlFor="username" className="form-label">Username</label>
              <input
                type="text"
                id="username"
                className="form-input"
                value={registerData.username}
                onChange={(e) => setRegisterData({...registerData, username: e.target.value})}
                required
                disabled={loading}
                minLength={3}
                maxLength={50}
                pattern="[a-zA-Z0-9_-]+"
                title="Username can only contain letters, numbers, hyphens, and underscores"
              />
              <small className="input-hint">
                Letters, numbers, hyphens, and underscores only (3-50 characters)
              </small>
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

            <div className="form-group">
              <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
              <input
                type="password"
                id="confirmPassword"
                className="form-input"
                value={registerData.confirmPassword}
                onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
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
              <label htmlFor="username" className="form-label">Username</label>
              <input
                type="text"
                id="username"
                className="form-input"
                value={loginData.username}
                onChange={(e) => setLoginData({...loginData, username: e.target.value})}
                required
                disabled={loading}
                ref={usernameInputRef}
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