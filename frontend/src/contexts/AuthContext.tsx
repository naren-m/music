import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

export interface User {
  id: string
  email: string
  name: string
  musicalBackground: 'beginner' | 'intermediate' | 'advanced'
  preferredRaga: string
  practiceGoal: string
  avatar?: string
  subscription?: {
    type: 'free' | 'premium' | 'professional'
    expiresAt?: Date
  }
  preferences: {
    language: 'en' | 'hi' | 'ta' | 'te' | 'kn'
    notifications: boolean
    autoRecording: boolean
    showDevanagari: boolean
  }
  progress: {
    totalPracticeTime: number
    currentStreak: number
    longestStreak: number
    completedExercises: number
    currentLevel: number
  }
}

export interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
}

export interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>
  signup: (data: SignupData) => Promise<void>
  logout: () => Promise<void>
  loginWithGoogle: () => Promise<void>
  loginAsGuest: () => Promise<void>
  updateUser: (updates: Partial<User>) => Promise<void>
  resetPassword: (email: string) => Promise<void>
  clearError: () => void
}

export interface SignupData {
  email: string
  password: string
  name: string
  musicalBackground: 'beginner' | 'intermediate' | 'advanced'
  preferredRaga: string
  practiceGoal: string
  language: 'en' | 'hi' | 'ta' | 'te' | 'kn'
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
    error: null
  })

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) {
        setState(prev => ({ ...prev, isLoading: false }))
        return
      }

      const response = await fetch('/api/auth/verify', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const user = await response.json()
        setState(prev => ({
          ...prev,
          user,
          isAuthenticated: true,
          isLoading: false
        }))
      } else {
        localStorage.removeItem('auth_token')
        setState(prev => ({ ...prev, isLoading: false }))
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Authentication check failed'
      }))
    }
  }

  const login = async (email: string, password: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      // Check if we're in development mode without backend API
      const isDevelopment = window.location.hostname === 'localhost'

      if (isDevelopment) {
        // Mock development login
        await new Promise(resolve => setTimeout(resolve, 1000)) // Simulate API delay

        const mockUser: User = {
          id: 'user-' + Date.now(),
          email: email,
          name: email.split('@')[0].replace(/[._]/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
          musicalBackground: 'intermediate',
          preferredRaga: 'Hamsadhvani',
          practiceGoal: 'Improve technique',
          preferences: {
            language: 'en',
            notifications: true,
            autoRecording: true,
            showDevanagari: true,
          },
          progress: {
            totalPracticeTime: 120,
            currentStreak: 5,
            longestStreak: 12,
            completedExercises: 25,
            currentLevel: 3,
          }
        }

        const token = 'dev-token-' + Date.now()
        localStorage.setItem('auth_token', token)

        setState(prev => ({
          ...prev,
          user: mockUser,
          isAuthenticated: true,
          isLoading: false
        }))
        return
      }

      // Production API call
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Login failed')
      }

      const { user, token } = await response.json()
      localStorage.setItem('auth_token', token)

      setState(prev => ({
        ...prev,
        user,
        isAuthenticated: true,
        isLoading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Login failed'
      }))
      throw error
    }
  }

  const signup = async (data: SignupData) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const response = await fetch('/api/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Signup failed')
      }

      const { user, token } = await response.json()
      localStorage.setItem('auth_token', token)

      setState(prev => ({
        ...prev,
        user,
        isAuthenticated: true,
        isLoading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Signup failed'
      }))
      throw error
    }
  }

  const logout = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (token) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
      }
    } catch (error) {
      console.error('Logout API call failed:', error)
    } finally {
      localStorage.removeItem('auth_token')
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
      })
    }
  }

  const loginWithGoogle = async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      // Implement Google OAuth flow
      window.location.href = '/api/auth/google'
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Google login failed'
      }))
      throw error
    }
  }

  const loginAsGuest = async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      // Check if we're in development mode without backend API
      const isDevelopment = window.location.hostname === 'localhost'

      if (isDevelopment) {
        // Mock development guest session
        await new Promise(resolve => setTimeout(resolve, 500)) // Simulate API delay

        const mockGuestUser: User = {
          id: 'guest-' + Date.now(),
          email: 'guest@example.com',
          name: 'Guest User',
          musicalBackground: 'beginner',
          preferredRaga: 'Kalyani',
          practiceGoal: 'Learn basics',
          preferences: {
            language: 'en',
            notifications: true,
            autoRecording: false,
            showDevanagari: true,
          },
          progress: {
            totalPracticeTime: 0,
            currentStreak: 0,
            longestStreak: 0,
            completedExercises: 0,
            currentLevel: 1,
          }
        }

        const token = 'guest-session-' + Date.now()
        localStorage.setItem('auth_token', token)

        setState(prev => ({
          ...prev,
          user: mockGuestUser,
          isAuthenticated: true,
          isLoading: false
        }))
        return
      }

      // Production API call
      const response = await fetch('/api/auth/guest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Guest login failed')
      }

      const { user, token } = await response.json()
      localStorage.setItem('auth_token', token)

      setState(prev => ({
        ...prev,
        user,
        isAuthenticated: true,
        isLoading: false
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Guest login failed'
      }))
      throw error
    }
  }

  const updateUser = async (updates: Partial<User>) => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch('/api/auth/user', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updates)
      })

      if (!response.ok) {
        throw new Error('Update failed')
      }

      const updatedUser = await response.json()
      setState(prev => ({
        ...prev,
        user: updatedUser
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Update failed'
      }))
      throw error
    }
  }

  const resetPassword = async (email: string) => {
    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.message || 'Password reset failed')
      }
    } catch (error) {
      throw error
    }
  }

  const clearError = () => {
    setState(prev => ({ ...prev, error: null }))
  }

  const value: AuthContextType = {
    ...state,
    login,
    signup,
    logout,
    loginWithGoogle,
    loginAsGuest,
    updateUser,
    resetPassword,
    clearError
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}