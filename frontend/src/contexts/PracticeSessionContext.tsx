import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react'
import { useAuth } from './AuthContext'
import { useAudio, PitchInfo } from './AudioContext'

export type ExerciseType = 'sarali' | 'janta' | 'alankaram' | 'gitam' | 'swarajathi' | 'varnam'

export interface PracticeSession {
  id: string
  userId: string
  exerciseType: ExerciseType
  exerciseId: string
  startTime: number
  endTime?: number
  duration: number
  raga: string
  tempo: number
  accuracy: number
  pitchStability: number
  rhythmAccuracy: number
  completionPercentage: number
  mistakes: PracticeMistake[]
  recordings: PracticeRecording[]
  notes: string[]
  score: number
  level: number
  isCompleted: boolean
}

export interface PracticeMistake {
  timestamp: number
  type: 'pitch' | 'rhythm' | 'duration' | 'transition'
  expected: any
  actual: any
  severity: 'minor' | 'major' | 'critical'
  feedback: string
}

export interface PracticeRecording {
  id: string
  timestamp: number
  duration: number
  audioBlob?: Blob
  pitchData: PitchInfo[]
  analysis: {
    averagePitch: number
    pitchRange: [number, number]
    stability: number
    accuracy: number
  }
}

export interface PracticeStats {
  totalSessions: number
  totalPracticeTime: number
  averageScore: number
  currentStreak: number
  longestStreak: number
  exerciseProgress: Record<ExerciseType, {
    level: number
    completedSessions: number
    averageScore: number
    bestScore: number
    totalTime: number
  }>
  weeklyProgress: {
    date: string
    sessions: number
    practiceTime: number
    score: number
  }[]
  monthlyGoals: {
    practiceTimeGoal: number
    practiceTimeActual: number
    sessionsGoal: number
    sessionsActual: number
  }
}

export interface PracticeSettings {
  autoRecording: boolean
  realTimeFeedback: boolean
  metronomeEnabled: boolean
  visualFeedback: boolean
  difficultyAdjustment: 'manual' | 'automatic'
  practiceReminders: boolean
  targetPracticeTime: number
  preferredTempo: number
  feedbackSensitivity: 'low' | 'medium' | 'high'
}

export interface PracticeContextType {
  currentSession: PracticeSession | null
  isSessionActive: boolean
  settings: PracticeSettings
  stats: PracticeStats | null

  startSession: (exerciseType: ExerciseType, exerciseId: string, config: Partial<PracticeSession>) => Promise<void>
  endSession: () => Promise<void>
  pauseSession: () => void
  resumeSession: () => void
  recordMistake: (mistake: Omit<PracticeMistake, 'timestamp'>) => void
  addRecording: (recording: Omit<PracticeRecording, 'id' | 'timestamp'>) => void
  updateSessionProgress: (progress: Partial<Pick<PracticeSession, 'accuracy' | 'pitchStability' | 'rhythmAccuracy' | 'completionPercentage'>>) => void
  addNote: (note: string) => void

  loadStats: () => Promise<void>
  updateSettings: (newSettings: Partial<PracticeSettings>) => Promise<void>
  getSessions: (filters?: { exerciseType?: ExerciseType; dateRange?: [Date, Date]; limit?: number }) => Promise<PracticeSession[]>
  getSessionById: (sessionId: string) => Promise<PracticeSession | null>
  deleteSession: (sessionId: string) => Promise<void>
  exportData: (format: 'json' | 'csv') => Promise<string>

  calculateScore: (session: PracticeSession) => number
  getRecommendations: () => Promise<string[]>
}

const defaultSettings: PracticeSettings = {
  autoRecording: true,
  realTimeFeedback: true,
  metronomeEnabled: false,
  visualFeedback: true,
  difficultyAdjustment: 'automatic',
  practiceReminders: true,
  targetPracticeTime: 30,
  preferredTempo: 120,
  feedbackSensitivity: 'medium'
}

const PracticeContext = createContext<PracticeContextType | undefined>(undefined)

export const usePracticeSession = () => {
  const context = useContext(PracticeContext)
  if (context === undefined) {
    throw new Error('usePracticeSession must be used within a PracticeSessionProvider')
  }
  return context
}

interface PracticeSessionProviderProps {
  children: ReactNode
}

export const PracticeSessionProvider: React.FC<PracticeSessionProviderProps> = ({ children }) => {
  const { user } = useAuth()
  const { currentPitch } = useAudio()

  const [currentSession, setCurrentSession] = useState<PracticeSession | null>(null)
  const [isSessionActive, setIsSessionActive] = useState(false)
  const [settings, setSettings] = useState<PracticeSettings>(defaultSettings)
  const [stats, setStats] = useState<PracticeStats | null>(null)
  const [sessionStartTime, setSessionStartTime] = useState<number | null>(null)

  useEffect(() => {
    if (user) {
      loadStats()
      loadSettings()
    }
  }, [user])

  const loadSettings = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch('/api/practice/settings', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const userSettings = await response.json()
        setSettings(prev => ({ ...prev, ...userSettings }))
      }
    } catch (error) {
      console.error('Failed to load practice settings:', error)
    }
  }

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch('/api/practice/stats', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const practiceStats = await response.json()
        setStats(practiceStats)
      }
    } catch (error) {
      console.error('Failed to load practice stats:', error)
    }
  }

  const generateSessionId = () => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  const startSession = async (exerciseType: ExerciseType, exerciseId: string, config: Partial<PracticeSession>) => {
    if (!user) throw new Error('User must be authenticated to start a session')

    const sessionId = generateSessionId()
    const startTime = Date.now()

    const newSession: PracticeSession = {
      id: sessionId,
      userId: user.id,
      exerciseType,
      exerciseId,
      startTime,
      duration: 0,
      raga: config.raga || 'Sankarabharanam',
      tempo: config.tempo || settings.preferredTempo,
      accuracy: 0,
      pitchStability: 0,
      rhythmAccuracy: 0,
      completionPercentage: 0,
      mistakes: [],
      recordings: [],
      notes: [],
      score: 0,
      level: config.level || 1,
      isCompleted: false,
      ...config
    }

    setCurrentSession(newSession)
    setIsSessionActive(true)
    setSessionStartTime(startTime)

    // Save session start to backend
    try {
      const token = localStorage.getItem('auth_token')
      await fetch('/api/practice/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          sessionId,
          exerciseType,
          exerciseId,
          startTime,
          config
        })
      })
    } catch (error) {
      console.error('Failed to save session start:', error)
    }
  }

  const endSession = async () => {
    if (!currentSession || !sessionStartTime) return

    const endTime = Date.now()
    const duration = endTime - sessionStartTime

    const finalSession: PracticeSession = {
      ...currentSession,
      endTime,
      duration,
      score: calculateScore(currentSession),
      isCompleted: true
    }

    setCurrentSession(finalSession)
    setIsSessionActive(false)

    // Save completed session to backend
    try {
      const token = localStorage.getItem('auth_token')
      await fetch(`/api/practice/sessions/${currentSession.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          endTime,
          duration,
          ...finalSession
        })
      })

      // Refresh stats after session completion
      await loadStats()
    } catch (error) {
      console.error('Failed to save session completion:', error)
    }

    // Clear current session after a delay to show results
    setTimeout(() => {
      setCurrentSession(null)
      setSessionStartTime(null)
    }, 5000)
  }

  const pauseSession = () => {
    setIsSessionActive(false)
  }

  const resumeSession = () => {
    setIsSessionActive(true)
  }

  const recordMistake = (mistake: Omit<PracticeMistake, 'timestamp'>) => {
    if (!currentSession) return

    const newMistake: PracticeMistake = {
      ...mistake,
      timestamp: Date.now()
    }

    setCurrentSession(prev => prev ? {
      ...prev,
      mistakes: [...prev.mistakes, newMistake]
    } : null)
  }

  const addRecording = (recording: Omit<PracticeRecording, 'id' | 'timestamp'>) => {
    if (!currentSession) return

    const newRecording: PracticeRecording = {
      id: `recording_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      ...recording
    }

    setCurrentSession(prev => prev ? {
      ...prev,
      recordings: [...prev.recordings, newRecording]
    } : null)
  }

  const updateSessionProgress = (progress: Partial<Pick<PracticeSession, 'accuracy' | 'pitchStability' | 'rhythmAccuracy' | 'completionPercentage'>>) => {
    if (!currentSession) return

    setCurrentSession(prev => prev ? {
      ...prev,
      ...progress
    } : null)
  }

  const addNote = (note: string) => {
    if (!currentSession) return

    setCurrentSession(prev => prev ? {
      ...prev,
      notes: [...prev.notes, note]
    } : null)
  }

  const calculateScore = useCallback((session: PracticeSession): number => {
    const baseScore = 100

    // Accuracy component (40% of score)
    const accuracyScore = session.accuracy * 0.4

    // Pitch stability component (30% of score)
    const stabilityScore = session.pitchStability * 0.3

    // Rhythm accuracy component (20% of score)
    const rhythmScore = session.rhythmAccuracy * 0.2

    // Completion bonus (10% of score)
    const completionBonus = session.completionPercentage * 0.1

    // Mistake penalties
    const mistakePenalties = session.mistakes.reduce((penalty, mistake) => {
      switch (mistake.severity) {
        case 'minor': return penalty - 1
        case 'major': return penalty - 3
        case 'critical': return penalty - 5
        default: return penalty
      }
    }, 0)

    const totalScore = Math.max(0, Math.min(100, baseScore * (accuracyScore + stabilityScore + rhythmScore + completionBonus) / 100 + mistakePenalties))

    return Math.round(totalScore)
  }, [])

  const getSessions = async (filters?: { exerciseType?: ExerciseType; dateRange?: [Date, Date]; limit?: number }): Promise<PracticeSession[]> => {
    try {
      const token = localStorage.getItem('auth_token')
      const params = new URLSearchParams()

      if (filters?.exerciseType) params.append('exerciseType', filters.exerciseType)
      if (filters?.dateRange) {
        params.append('startDate', filters.dateRange[0].toISOString())
        params.append('endDate', filters.dateRange[1].toISOString())
      }
      if (filters?.limit) params.append('limit', filters.limit.toString())

      const response = await fetch(`/api/practice/sessions?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        return await response.json()
      }

      throw new Error('Failed to fetch sessions')
    } catch (error) {
      console.error('Failed to get practice sessions:', error)
      return []
    }
  }

  const getSessionById = async (sessionId: string): Promise<PracticeSession | null> => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch(`/api/practice/sessions/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        return await response.json()
      }

      return null
    } catch (error) {
      console.error('Failed to get session:', error)
      return null
    }
  }

  const deleteSession = async (sessionId: string) => {
    try {
      const token = localStorage.getItem('auth_token')
      await fetch(`/api/practice/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      await loadStats()
    } catch (error) {
      console.error('Failed to delete session:', error)
      throw error
    }
  }

  const updateSettings = async (newSettings: Partial<PracticeSettings>) => {
    const updatedSettings = { ...settings, ...newSettings }
    setSettings(updatedSettings)

    try {
      const token = localStorage.getItem('auth_token')
      await fetch('/api/practice/settings', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(newSettings)
      })
    } catch (error) {
      console.error('Failed to update settings:', error)
      throw error
    }
  }

  const exportData = async (format: 'json' | 'csv'): Promise<string> => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch(`/api/practice/export?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        return await response.text()
      }

      throw new Error('Export failed')
    } catch (error) {
      console.error('Failed to export data:', error)
      throw error
    }
  }

  const getRecommendations = async (): Promise<string[]> => {
    try {
      const token = localStorage.getItem('auth_token')
      const response = await fetch('/api/practice/recommendations', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        return data.recommendations || []
      }

      return []
    } catch (error) {
      console.error('Failed to get recommendations:', error)
      return []
    }
  }

  const value: PracticeContextType = {
    currentSession,
    isSessionActive,
    settings,
    stats,
    startSession,
    endSession,
    pauseSession,
    resumeSession,
    recordMistake,
    addRecording,
    updateSessionProgress,
    addNote,
    loadStats,
    updateSettings,
    getSessions,
    getSessionById,
    deleteSession,
    exportData,
    calculateScore,
    getRecommendations
  }

  return (
    <PracticeContext.Provider value={value}>
      {children}
    </PracticeContext.Provider>
  )
}