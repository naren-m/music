// Central type definitions export for the Carnatic Music Learning Platform
// This file consolidates all type definitions for easy importing throughout the application

// Import types from individual modules
import type * as AudioTypes from './audio.types'
import type * as ExerciseTypes from './exercise.types'

// Audio-related types
export type {
  // Core audio types
  NoteString,
  SwaraName,
  OctaveNumber,
  AudioDeviceInfo,
  AudioConfig,
  PitchInfo,
  AudioAnalysis,
  AudioQuality,
  RecordingMetadata,
  AudioRecording,
  CalibrationData,
  AudioProcessingOptions,
  RealTimeFeedback,
  AudioVisualizationData,
  TuningReference,
  AudioEffect,
  AudioMixer,
  SoundSynthesis,
  AudioWorkletMessage,
  PerformanceMetrics,

  // Carnatic music specific audio types
  RagaDefinition,
  TalaDefinition,
  GamakaPattern,

  // Utility audio types
  AudioEventType,
  AudioEvent,
  AudioQualityLevel,
  AudioFormat,

  // Browser audio types
  AudioContext,
  MediaStream,
  AudioNode,
  AnalyserNode,
  OscillatorNode,
  GainNode,
  AudioBuffer,
  AudioBufferSourceNode,
  MediaStreamAudioSourceNode,
  BiquadFilterNode,
  ConvolverNode,
  DynamicsCompressorNode,
  WaveShaperNode,
  DelayNode
} from './audio.types'

// Exercise and practice-related types
export type {
  // Base exercise types
  ExerciseType,
  DifficultyLevel,
  ExerciseMode,
  BaseExercise,
  NotationElement,

  // Specific exercise types
  SaraliVarisaiExercise,
  JantaVarisaiExercise,
  AlankaramExercise,
  GitamExercise,
  SwarajathiExercise,
  VarnamExercise,
  Exercise,

  // Practice session types
  PracticeSessionConfig,
  PracticeAttempt,
  PerformanceAnalysis,
  PerformanceMistake,
  DetailedFeedback,

  // Learning progress types
  ExerciseProgress,
  LearningPath,
  UserLearningProfile,

  // Assessment types
  Assessment,
  AssessmentAttempt,

  // Gamification types
  Achievement,
  Badge,

  // Teacher and lesson types
  TeacherProfile,
  TeacherReview,
  Lesson,

  // Utility exercise types
  ExerciseFilter,
  ProgressMetric,
  FeedbackType
} from './exercise.types'

// Context types (re-exported from context files)
export type {
  User,
  AuthState,
  AuthContextType,
  SignupData
} from '../contexts/AuthContext'

export type {
  AudioState,
  AudioContextType
} from '../contexts/AudioContext'

export type {
  PracticeSession,
  PracticeMistake,
  PracticeRecording,
  PracticeStats,
  PracticeSettings,
  PracticeContextType
} from '../contexts/PracticeSessionContext'

// Service types (re-exported from service files)
export type {
  AudioAnalysisResult,
  RecordingData,
  VoiceCalibrationData
} from '../services/audioService'

export type {
  ExerciseDefinition,
  ProgressData,
  FeedbackData
} from '../services/practiceService'

// Component prop types for commonly used components
export interface BaseComponentProps {
  className?: string
  children?: React.ReactNode
}

export interface ExerciseComponentProps extends BaseComponentProps {
  exercise: Exercise
  onStart?: () => void
  onComplete?: (result: PracticeAttempt) => void
  onCancel?: () => void
}

export interface AudioComponentProps extends BaseComponentProps {
  audioConfig?: Partial<AudioConfig>
  onAudioData?: (data: AudioVisualizationData) => void
  onPitchDetected?: (pitch: PitchInfo) => void
  onError?: (error: string) => void
}

export interface PracticeComponentProps extends BaseComponentProps {
  sessionConfig: PracticeSessionConfig
  onProgressUpdate?: (progress: Partial<PerformanceAnalysis>) => void
  onFeedback?: (feedback: DetailedFeedback) => void
  onComplete?: (session: PracticeSession) => void
}

// Form types for various input scenarios
export interface LoginFormData {
  email: string
  password: string
  rememberMe: boolean
}

export interface SignupFormData {
  email: string
  password: string
  confirmPassword: string
  name: string
  musicalBackground: 'beginner' | 'intermediate' | 'advanced'
  preferredRaga: string
  practiceGoal: string
  language: 'en' | 'hi' | 'ta' | 'te' | 'kn'
  agreeToTerms: boolean
}

export interface ProfileUpdateData {
  name?: string
  email?: string
  musicalBackground?: 'beginner' | 'intermediate' | 'advanced'
  preferredRaga?: string
  practiceGoal?: string
  language?: 'en' | 'hi' | 'ta' | 'te' | 'kn'
  preferences?: {
    notifications: boolean
    autoRecording: boolean
    showDevanagari: boolean
  }
}

export interface FeedbackFormData {
  rating: number
  difficulty: number
  clarity: number
  usefulness: number
  comments: string
  suggestions: string
  wouldRecommend: boolean
}

// API response types
export interface APIResponse<T> {
  success: boolean
  data: T
  message?: string
  error?: string
  meta?: {
    pagination?: {
      page: number
      limit: number
      total: number
      hasNext: boolean
      hasPrev: boolean
    }
    filters?: any
    sort?: string
  }
}

export interface APIError {
  message: string
  code: string
  statusCode: number
  details?: any
  timestamp: number
}

// Navigation and routing types
export interface NavItem {
  name: string
  nameDevanagari: string
  href: string
  icon: any // React component type
  description?: string
  children?: NavItem[]
  badge?: string
  isNew?: boolean
  requiresAuth?: boolean
  requiresSubscription?: boolean
}

export interface BreadcrumbItem {
  name: string
  href?: string
  current: boolean
}

// Theme and styling types
export interface ThemeColors {
  primary: {
    50: string
    100: string
    200: string
    300: string
    400: string
    500: string
    600: string
    700: string
    800: string
    900: string
  }
  secondary: {
    50: string
    100: string
    200: string
    300: string
    400: string
    500: string
    600: string
    700: string
    800: string
    900: string
  }
  accent: {
    50: string
    100: string
    200: string
    300: string
    400: string
    500: string
    600: string
    700: string
    800: string
    900: string
  }
  neutral: {
    50: string
    100: string
    200: string
    300: string
    400: string
    500: string
    600: string
    700: string
    800: string
    900: string
  }
  cultural: {
    saffron: string
    deepOrange: string
    gold: string
    maroon: string
    earthyBrown: string
  }
}

export interface CulturalTheme {
  colors: ThemeColors
  fonts: {
    primary: string // English fonts
    devanagari: string // Devanagari fonts
    tamil: string // Tamil fonts
    telugu: string // Telugu fonts
    kannada: string // Kannada fonts
  }
  spacing: {
    xs: string
    sm: string
    md: string
    lg: string
    xl: string
    '2xl': string
  }
  borderRadius: {
    sm: string
    md: string
    lg: string
    full: string
  }
  shadows: {
    sm: string
    md: string
    lg: string
    xl: string
  }
}

// Language and localization types
export type SupportedLanguage = 'en' | 'hi' | 'ta' | 'te' | 'kn'

export interface LocalizedText {
  en: string
  hi?: string
  ta?: string
  te?: string
  kn?: string
}

export interface CulturalContent {
  title: LocalizedText
  description: LocalizedText
  significance?: LocalizedText
  pronunciation?: {
    [key in SupportedLanguage]?: string
  }
  etymology?: LocalizedText
}

// Utility types for common patterns
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

export type RequireOnly<T, K extends keyof T> = Partial<T> & Required<Pick<T, K>>

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

export type Nullable<T> = T | null

export type AsyncState<T> = {
  data: T | null
  loading: boolean
  error: string | null
}

// Event handler types
export type EventHandler<T = void> = (data: T) => void | Promise<void>

export type AudioEventHandler = EventHandler<AudioEvent>
export type PracticeEventHandler = EventHandler<PracticeSession>
export type ExerciseEventHandler = EventHandler<Exercise>
export type ErrorEventHandler = EventHandler<APIError>

// Configuration types
export interface AppConfig {
  api: {
    baseUrl: string
    timeout: number
    retries: number
  }
  audio: AudioConfig
  features: {
    realTimeFeedback: boolean
    gamification: boolean
    socialFeatures: boolean
    aiAssistant: boolean
    offlineMode: boolean
  }
  cultural: {
    defaultLanguage: SupportedLanguage
    supportedLanguages: SupportedLanguage[]
    showDevanagari: boolean
    culturalNotes: boolean
  }
  performance: {
    maxConcurrentRecordings: number
    audioBufferSize: number
    analysisInterval: number
    cacheSize: number
  }
}

// Default export for convenient importing
export default {
  // Re-export everything for default import usage
}

// Type guards for runtime type checking
export const isExerciseType = (value: string): value is ExerciseType => {
  return ['sarali', 'janta', 'alankaram', 'gitam', 'swarajathi', 'varnam', 'kriti', 'avarohana', 'melakartha'].includes(value)
}

export const isDifficultyLevel = (value: string): value is DifficultyLevel => {
  return ['beginner', 'intermediate', 'advanced', 'expert'].includes(value)
}

export const isSupportedLanguage = (value: string): value is SupportedLanguage => {
  return ['en', 'hi', 'ta', 'te', 'kn'].includes(value)
}

export const isPitchInfo = (value: any): value is PitchInfo => {
  return typeof value === 'object' &&
    typeof value.frequency === 'number' &&
    typeof value.note === 'string' &&
    typeof value.octave === 'number' &&
    typeof value.cents === 'number' &&
    typeof value.confidence === 'number' &&
    typeof value.timestamp === 'number'
}