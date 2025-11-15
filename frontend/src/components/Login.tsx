import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import '../styles/components/Login.css'
import { authApi } from '../api'
import type { User } from '../types/user'
import { sanitizeString } from '../utils/validation'
import { getErrorMessage } from '../utils/errorHandling'

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
  const { t } = useTranslation(['auth'])
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
      setError(getErrorMessage(err, 'Login failed'))
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
      setError(t('auth:errors.passwordMismatch'))
      setLoading(false)
      return
    }

    try {
      const sanitizedName = sanitizeString(registerData.name, 100)
      const sanitizedUsername = sanitizeString(registerData.username.trim(), 50)
      const user = await authApi.register(sanitizedName, sanitizedUsername, registerData.password)
      onLogin(user)
    } catch (err) {
      setError(getErrorMessage(err, 'Registration failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>{isRegister ? t('auth:register.title') : t('auth:login.title')}</h2>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {isRegister ? (
          <form onSubmit={handleRegister} className="auth-form">
            <div className="form-group">
              <label htmlFor="name" className="form-label">{t('auth:fields.name')}</label>
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
              <label htmlFor="username" className="form-label">{t('auth:fields.username')}</label>
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
                title={t('auth:validation.usernamePattern')}
              />
              <small className="input-hint">
                {t('auth:validation.usernameHint')}
              </small>
            </div>
            <div className="form-group">
              <label htmlFor="password" className="form-label">{t('auth:fields.password')}</label>
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
              <label htmlFor="confirmPassword" className="form-label">{t('auth:fields.confirmPassword')}</label>
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
              {loading ? t('auth:register.submitting') : t('auth:register.submit')}
            </button>
          </form>
        ) : (
          <form onSubmit={handleLogin} className="auth-form">
            <div className="form-group">
              <label htmlFor="username" className="form-label">{t('auth:fields.username')}</label>
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
              <label htmlFor="password" className="form-label">{t('auth:fields.password')}</label>
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
              {loading ? t('auth:login.submitting') : t('auth:login.submit')}
            </button>
          </form>
        )}

        <div className="auth-switch">
          {isRegister ? (
            <p>
              {t('auth:register.hasAccount')}{' '}
              <button
                type="button"
                onClick={() => setIsRegister(false)}
                className="link-button"
                disabled={loading}
              >
                {t('auth:login.submit')}
              </button>
            </p>
          ) : (
            <p>
              {t('auth:login.noAccount')}{' '}
              <button
                type="button"
                onClick={() => setIsRegister(true)}
                className="link-button"
                disabled={loading}
              >
                {t('auth:register.submit')}
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}