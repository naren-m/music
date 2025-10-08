import { PracticeSession, ExerciseType, PracticeStats, PracticeMistake } from '../contexts/PracticeSessionContext'

export interface ExerciseDefinition {
  id: string
  type: ExerciseType
  name: string
  nameDevanagari: string
  description: string
  level: number
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  raga: string
  tempo_range: [number, number]
  duration_minutes: number
  learning_objectives: string[]
  prerequisites: string[]
  swaras: string[]
  patterns?: any[]
  cultural_significance: string
  teaching_notes: string[]
}

export interface ProgressData {
  exercise_id: string
  user_id: string
  current_level: number
  completion_percentage: number
  best_score: number
  total_attempts: number
  total_practice_time: number
  average_accuracy: number
  improvement_rate: number
  last_practiced: string
  next_milestone: {
    description: string
    target_score: number
    estimated_practice_time: number
  }
}

export interface LearningPath {
  id: string
  name: string
  description: string
  estimated_weeks: number
  exercises: {
    exercise_id: string
    order: number
    min_score_to_progress: number
    estimated_hours: number
  }[]
  prerequisites: string[]
  learning_outcomes: string[]
}

export interface FeedbackData {
  session_id: string
  overall_score: number
  detailed_feedback: {
    pitch_accuracy: {
      score: number
      feedback: string
      specific_notes: {
        note: string
        accuracy: number
        suggestion: string
      }[]
    }
    rhythm_accuracy: {
      score: number
      feedback: string
      timing_analysis: {
        beat: number
        expected_time: number
        actual_time: number
        deviation: number
      }[]
    }
    expression: {
      score: number
      feedback: string
      dynamics_analysis: number[]
      phrasing_suggestions: string[]
    }
    cultural_authenticity: {
      score: number
      feedback: string
      raga_adherence: number
      style_recommendations: string[]
    }
  }
  improvement_suggestions: string[]
  next_practice_focus: string[]
}

class PracticeService {
  private baseUrl = '/api/practice'

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('auth_token')
    const url = `${this.baseUrl}${endpoint}`

    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
    }

    const response = await fetch(url, config)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Get all available exercises
   */
  async getExercises(filters?: {
    type?: ExerciseType
    difficulty?: 'beginner' | 'intermediate' | 'advanced'
    raga?: string
    user_level?: number
  }): Promise<ExerciseDefinition[]> {
    const params = new URLSearchParams()
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          params.append(key, value.toString())
        }
      })
    }

    const queryString = params.toString()
    const url = queryString ? `/exercises?${queryString}` : '/exercises'

    return this.request<ExerciseDefinition[]>(url)
  }

  /**
   * Get a specific exercise by ID
   */
  async getExercise(exerciseId: string): Promise<ExerciseDefinition> {
    return this.request<ExerciseDefinition>(`/exercises/${exerciseId}`)
  }

  /**
   * Get user's progress for all exercises
   */
  async getUserProgress(): Promise<ProgressData[]> {
    return this.request<ProgressData[]>('/progress')
  }

  /**
   * Get user's progress for specific exercise
   */
  async getExerciseProgress(exerciseId: string): Promise<ProgressData> {
    return this.request<ProgressData>(`/progress/${exerciseId}`)
  }

  /**
   * Update exercise progress
   */
  async updateProgress(exerciseId: string, progressData: Partial<ProgressData>): Promise<ProgressData> {
    return this.request<ProgressData>(`/progress/${exerciseId}`, {
      method: 'PATCH',
      body: JSON.stringify(progressData),
    })
  }

  /**
   * Get practice statistics
   */
  async getStats(timeRange?: 'week' | 'month' | 'year' | 'all'): Promise<PracticeStats> {
    const params = timeRange ? `?range=${timeRange}` : ''
    return this.request<PracticeStats>(`/stats${params}`)
  }

  /**
   * Get practice sessions
   */
  async getSessions(filters?: {
    exercise_type?: ExerciseType
    exercise_id?: string
    date_range?: [string, string]
    limit?: number
    offset?: number
    include_recordings?: boolean
  }): Promise<PracticeSession[]> {
    const params = new URLSearchParams()
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          if (Array.isArray(value)) {
            params.append(`${key}[]`, value.join(','))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }

    const queryString = params.toString()
    const url = queryString ? `/sessions?${queryString}` : '/sessions'

    return this.request<PracticeSession[]>(url)
  }

  /**
   * Get a specific practice session
   */
  async getSession(sessionId: string): Promise<PracticeSession> {
    return this.request<PracticeSession>(`/sessions/${sessionId}`)
  }

  /**
   * Create a new practice session
   */
  async createSession(sessionData: Partial<PracticeSession>): Promise<PracticeSession> {
    return this.request<PracticeSession>('/sessions', {
      method: 'POST',
      body: JSON.stringify(sessionData),
    })
  }

  /**
   * Update an existing practice session
   */
  async updateSession(sessionId: string, sessionData: Partial<PracticeSession>): Promise<PracticeSession> {
    return this.request<PracticeSession>(`/sessions/${sessionId}`, {
      method: 'PATCH',
      body: JSON.stringify(sessionData),
    })
  }

  /**
   * Delete a practice session
   */
  async deleteSession(sessionId: string): Promise<void> {
    await this.request(`/sessions/${sessionId}`, {
      method: 'DELETE',
    })
  }

  /**
   * Get detailed feedback for a session
   */
  async getSessionFeedback(sessionId: string): Promise<FeedbackData> {
    return this.request<FeedbackData>(`/sessions/${sessionId}/feedback`)
  }

  /**
   * Get personalized recommendations
   */
  async getRecommendations(): Promise<{
    next_exercises: {
      exercise_id: string
      reason: string
      estimated_difficulty: number
      estimated_time: number
    }[]
    focus_areas: {
      area: string
      current_score: number
      target_score: number
      practice_suggestions: string[]
    }[]
    practice_schedule: {
      day: string
      recommended_duration: number
      focus_exercises: string[]
    }[]
  }> {
    return this.request('/recommendations')
  }

  /**
   * Get available learning paths
   */
  async getLearningPaths(): Promise<LearningPath[]> {
    return this.request<LearningPath[]>('/learning-paths')
  }

  /**
   * Get specific learning path
   */
  async getLearningPath(pathId: string): Promise<LearningPath> {
    return this.request<LearningPath>(`/learning-paths/${pathId}`)
  }

  /**
   * Enroll in a learning path
   */
  async enrollInLearningPath(pathId: string): Promise<{
    enrollment_id: string
    path_id: string
    user_id: string
    started_at: string
    estimated_completion: string
    current_exercise: string
  }> {
    return this.request('/learning-paths/enroll', {
      method: 'POST',
      body: JSON.stringify({ path_id: pathId }),
    })
  }

  /**
   * Get user's learning path progress
   */
  async getLearningPathProgress(pathId: string): Promise<{
    path_id: string
    overall_progress: number
    current_exercise: string
    completed_exercises: string[]
    estimated_time_remaining: number
    milestones_completed: number
    total_milestones: number
  }> {
    return this.request(`/learning-paths/${pathId}/progress`)
  }

  /**
   * Submit practice goals
   */
  async setGoals(goals: {
    daily_practice_minutes: number
    weekly_sessions: number
    target_exercises: string[]
    skill_focus_areas: string[]
    target_completion_date?: string
  }): Promise<void> {
    await this.request('/goals', {
      method: 'POST',
      body: JSON.stringify(goals),
    })
  }

  /**
   * Get user's practice goals
   */
  async getGoals(): Promise<{
    daily_practice_minutes: number
    weekly_sessions: number
    target_exercises: string[]
    skill_focus_areas: string[]
    target_completion_date?: string
    current_progress: {
      daily_progress: number
      weekly_progress: number
      exercise_completion: { [key: string]: number }
    }
  }> {
    return this.request('/goals')
  }

  /**
   * Get practice streaks and achievements
   */
  async getAchievements(): Promise<{
    current_streak: number
    longest_streak: number
    total_practice_days: number
    badges: {
      id: string
      name: string
      description: string
      icon: string
      earned_at: string
      rarity: 'common' | 'rare' | 'epic' | 'legendary'
    }[]
    milestones: {
      name: string
      description: string
      progress: number
      target: number
      reward: string
    }[]
  }> {
    return this.request('/achievements')
  }

  /**
   * Export practice data
   */
  async exportData(format: 'json' | 'csv' | 'pdf', options?: {
    include_audio?: boolean
    date_range?: [string, string]
    exercise_types?: ExerciseType[]
  }): Promise<Blob> {
    const params = new URLSearchParams({ format })
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        if (value !== undefined) {
          if (Array.isArray(value)) {
            params.append(key, value.join(','))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }

    const token = localStorage.getItem('auth_token')
    const response = await fetch(`${this.baseUrl}/export?${params.toString()}`, {
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
    })

    if (!response.ok) {
      throw new Error('Export failed')
    }

    return response.blob()
  }

  /**
   * Get practice analytics
   */
  async getAnalytics(timeRange: 'week' | 'month' | 'quarter' | 'year'): Promise<{
    practice_time_trend: { date: string; minutes: number }[]
    accuracy_trend: { date: string; accuracy: number }[]
    exercise_distribution: { exercise_type: string; sessions: number; total_time: number }[]
    improvement_metrics: {
      pitch_accuracy: { before: number; after: number; change: number }
      rhythm_accuracy: { before: number; after: number; change: number }
      overall_score: { before: number; after: number; change: number }
    }
    consistency_score: number
    focus_time_analysis: {
      optimal_session_duration: number
      peak_performance_times: string[]
      fatigue_indicators: string[]
    }
  }> {
    return this.request(`/analytics?range=${timeRange}`)
  }

  /**
   * Submit feedback on an exercise
   */
  async submitExerciseFeedback(exerciseId: string, feedback: {
    rating: number
    difficulty_rating: number
    clarity_rating: number
    usefulness_rating: number
    comments?: string
    suggestions?: string
  }): Promise<void> {
    await this.request(`/exercises/${exerciseId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(feedback),
    })
  }

  /**
   * Get cultural context and teaching notes for raga
   */
  async getRagaInfo(ragaName: string): Promise<{
    name: string
    nameDevanagari: string
    melakarta?: number
    arohanam: string[]
    avarohanam: string[]
    characteristics: string
    cultural_significance: string
    famous_compositions: {
      name: string
      composer: string
      difficulty: string
    }[]
    teaching_notes: string[]
    practice_tips: string[]
  }> {
    return this.request(`/ragas/${ragaName}`)
  }

  /**
   * Get AI-powered practice suggestions
   */
  async getAIPracticeSuggestions(recentSessions: string[]): Promise<{
    suggested_exercises: string[]
    focus_areas: string[]
    difficulty_adjustments: {
      exercise_id: string
      suggested_level: number
      reason: string
    }[]
    practice_schedule: {
      optimal_session_length: number
      recommended_frequency: number
      best_practice_times: string[]
    }
    technique_tips: string[]
  }> {
    return this.request('/ai-suggestions', {
      method: 'POST',
      body: JSON.stringify({ recent_sessions: recentSessions }),
    })
  }
}

// Export singleton instance
export const practiceService = new PracticeService()

// Utility functions
export const calculatePracticeStreak = (sessions: PracticeSession[]): { current: number; longest: number } => {
  if (!sessions.length) return { current: 0, longest: 0 }

  const sortedSessions = sessions
    .filter(s => s.isCompleted)
    .sort((a, b) => b.startTime - a.startTime)

  const practiceDays = new Set(
    sortedSessions.map(s => new Date(s.startTime).toDateString())
  )

  const practiceArray = Array.from(practiceDays).sort((a, b) =>
    new Date(b).getTime() - new Date(a).getTime()
  )

  let currentStreak = 0
  let longestStreak = 0
  let tempStreak = 0

  const today = new Date().toDateString()
  const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toDateString()

  // Calculate current streak
  for (let i = 0; i < practiceArray.length; i++) {
    const practiceDate = practiceArray[i]
    const expectedDate = i === 0 ?
      (practiceDate === today ? today : yesterday) :
      new Date(Date.now() - (i + 1) * 24 * 60 * 60 * 1000).toDateString()

    if (practiceDate === expectedDate) {
      currentStreak++
    } else {
      break
    }
  }

  // Calculate longest streak
  let consecutiveDays = 1
  for (let i = 1; i < practiceArray.length; i++) {
    const currentDate = new Date(practiceArray[i])
    const prevDate = new Date(practiceArray[i - 1])
    const dayDiff = (prevDate.getTime() - currentDate.getTime()) / (24 * 60 * 60 * 1000)

    if (dayDiff === 1) {
      consecutiveDays++
    } else {
      longestStreak = Math.max(longestStreak, consecutiveDays)
      consecutiveDays = 1
    }
  }
  longestStreak = Math.max(longestStreak, consecutiveDays)

  return { current: currentStreak, longest: longestStreak }
}

export const formatPracticeTime = (minutes: number): string => {
  if (minutes < 60) {
    return `${minutes}m`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
}

export const getScoreColor = (score: number): string => {
  if (score >= 90) return 'text-green-600'
  if (score >= 75) return 'text-blue-600'
  if (score >= 60) return 'text-yellow-600'
  if (score >= 40) return 'text-orange-600'
  return 'text-red-600'
}

export const categorizeError = (mistake: PracticeMistake): {
  category: string
  description: string
  improvement_tip: string
} => {
  const errorTypes = {
    pitch: {
      category: 'Pitch Accuracy',
      description: 'Notes sung at incorrect frequencies',
      improvement_tip: 'Practice with a reference tone and focus on matching the exact pitch'
    },
    rhythm: {
      category: 'Rhythm Accuracy',
      description: 'Notes played at incorrect timing',
      improvement_tip: 'Practice with a metronome to improve timing consistency'
    },
    duration: {
      category: 'Note Duration',
      description: 'Notes held for incorrect lengths',
      improvement_tip: 'Count beats carefully and practice sustaining notes for the correct duration'
    },
    transition: {
      category: 'Note Transitions',
      description: 'Smooth transitions between notes need improvement',
      improvement_tip: 'Practice slow, deliberate transitions between notes before increasing tempo'
    }
  }

  return errorTypes[mistake.type] || {
    category: 'General',
    description: 'Areas for improvement identified',
    improvement_tip: 'Continue practicing to refine your technique'
  }
}

export default practiceService