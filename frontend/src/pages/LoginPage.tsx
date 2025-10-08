import React from 'react'
import { useNavigate } from 'react-router-dom'
import { LoginForm } from '../components/auth/LoginForm'
import { useAuth } from '../contexts/AuthContext'

const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const { login, loginAsGuest } = useAuth()

  const handleLogin = async (credentials: { email: string; password: string }) => {
    try {
      await login(credentials.email, credentials.password)
      navigate('/')
    } catch (error) {
      throw error // Re-throw to let LoginForm handle the error display
    }
  }

  const handleGuestSession = async () => {
    try {
      // Use the AuthContext loginAsGuest function which handles mock data in development
      await loginAsGuest()
      navigate('/')
    } catch (error) {
      console.error('Guest session failed:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-saffron-400 to-deepOrange-400 bg-clip-text text-transparent mb-2">
            संगीत शाला
          </h1>
          <p className="text-gray-400">Welcome back to your musical journey</p>
        </div>
        <LoginForm
          onLogin={handleLogin}
          onGuestSession={handleGuestSession}
        />
      </div>
    </div>
  )
}

export default LoginPage