// Exercise and practice-related type definitions for the Carnatic Music Learning Platform

import { SwaraName, NoteString, RagaDefinition, TalaDefinition, GamakaPattern, PitchInfo } from './audio.types'

export type ExerciseType = 'sarali' | 'janta' | 'alankaram' | 'gitam' | 'swarajathi' | 'varnam' | 'kriti' | 'avarohana' | 'melakartha'

export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert'

export type ExerciseMode = 'learn' | 'practice' | 'test' | 'performance'

export interface BaseExercise {
  id: string
  type: ExerciseType
  name: string
  nameDevanagari: string
  description: string
  culturalSignificance: string
  difficulty: DifficultyLevel
  level: number
  estimatedDuration: number // minutes
  prerequisites: string[] // Exercise IDs
  learningObjectives: string[]
  teachingNotes: string[]
  raga: string
  tala?: string
  tempo: {
    min: number
    max: number
    default: number
  }
  swaras: SwaraName[]
  notation: NotationElement[]
  audioReference?: string // URL to reference audio
  videoReference?: string // URL to instructional video
  culturalContext: {
    origin: string
    traditionalUsage: string
    spiritualSignificance?: string
    historicalNotes: string
  }
  tags: string[]
  createdAt: number
  updatedAt: number
}

export interface NotationElement {
  swara: SwaraName
  duration: number // beats
  octave: number
  gamaka?: GamakaPattern
  emphasis?: 'light' | 'medium' | 'strong'
  lyrics?: string
  lyricsMeaning?: string
}

// Specific exercise type definitions
export interface SaraliVarisaiExercise extends BaseExercise {
  type: 'sarali'
  pattern: 'ascending' | 'descending' | 'mixed'
  repetitions: number
  variations: {
    name: string
    pattern: SwaraName[]
    emphasis: ('light' | 'medium' | 'strong')[]
  }[]
}

export interface JantaVarisaiExercise extends BaseExercise {
  type: 'janta'
  doubleNotes: {
    first: SwaraName
    second: SwaraName
    transition: 'smooth' | 'distinct'
    emphasis: 'first' | 'second' | 'equal'
  }[]
  transitionPatterns: string[]
  rhythmicFlexibility: boolean
}

export interface AlankaramExercise extends BaseExercise {
  type: 'alankaram'
  patternNumber: number // 1-35 traditional patterns
  ornamentationType: 'simple' | 'compound' | 'complex'
  ragaIntegration: boolean
  patterns: {
    name: string
    notation: NotationElement[]
    difficulty: DifficultyLevel
    culturalNotes: string
  }[]
}

export interface GitamExercise extends BaseExercise {
  type: 'gitam'
  composition: {
    pallavi: NotationElement[]
    anupallavi?: NotationElement[]
    charanam?: NotationElement[]
  }
  composer: string
  lyrics: {
    text: string
    meaning: string
    language: 'sanskrit' | 'tamil' | 'telugu' | 'kannada'
  }
  devotionalContext: {
    deity?: string
    mood: string
    occasion: string
  }
}

export interface SwarajathiExercise extends BaseExercise {
  type: 'swarajathi'
  jathi: number // 3, 4, 5, 7, or 9
  composition: {
    pallavi: NotationElement[]
    anupallavi: NotationElement[]
    charanams: NotationElement[][]
  }
  sahityam: boolean // Whether it has lyrics
  technichalAspects: {
    gamakas: GamakaPattern[]
    phrases: string[]
    improvisation: boolean
  }
}

export interface VarnamExercise extends BaseExercise {
  type: 'varnam'
  varnamType: 'tana' | 'pada'
  composition: {
    pallavi: NotationElement[]
    anupallavi: NotationElement[]
    muktayi: NotationElement[]
    charanams: NotationElement[][]
    ettugada?: NotationElement[]
  }
  swara_sequences: NotationElement[][]
  kalpana_swara_sections: boolean
  performanceNotes: string[]
}

export type Exercise = SaraliVarisaiExercise | JantaVarisaiExercise | AlankaramExercise | GitamExercise | SwarajathiExercise | VarnamExercise

// Practice session types
export interface PracticeSessionConfig {
  exerciseId: string
  mode: ExerciseMode
  tempo: number
  repetitions?: number
  focusAreas: string[]
  enableFeedback: boolean
  enableRecording: boolean
  difficultyAdjustments?: {
    simplifyGamakas: boolean
    reduceTempo: boolean
    provideMoreGuidance: boolean
  }
}

export interface PracticeAttempt {
  id: string
  sessionId: string
  exerciseId: string
  startTime: number
  endTime: number
  duration: number
  userPerformance: {
    pitchData: PitchInfo[]
    audioBlob?: Blob
    notation: NotationElement[]
  }
  analysis: PerformanceAnalysis
  score: number
  feedback: DetailedFeedback
  mistakes: PerformanceMistake[]
  improvements: string[]
}

export interface PerformanceAnalysis {
  overall: {
    accuracy: number // 0-1
    completeness: number // 0-1
    expression: number // 0-1
    culturalAuthenticity: number // 0-1
  }
  pitch: {
    accuracy: number // 0-1
    stability: number // 0-1
    intonation: number // 0-1
    ragaCompliance: number // 0-1
  }
  rhythm: {
    accuracy: number // 0-1
    consistency: number // 0-1
    talaCompliance: number // 0-1
  }
  technique: {
    gamakaExecution: number // 0-1
    breathControl: number // 0-1
    voiceQuality: number // 0-1
  }
  specific: {
    noteAccuracy: {
      swara: SwaraName
      expected: number // Hz
      actual: number // Hz
      accuracy: number // 0-1
    }[]
    rhythmDeviations: {
      beat: number
      expectedTime: number
      actualTime: number
      deviation: number // milliseconds
    }[]
    gamakaAnalysis: {
      pattern: GamakaPattern
      executionQuality: number // 0-1
      timing: number // 0-1
      pitch: number // 0-1
    }[]
  }
}

export interface PerformanceMistake {
  id: string
  timestamp: number
  type: 'pitch' | 'rhythm' | 'gamaka' | 'pronunciation' | 'expression' | 'cultural'
  severity: 'minor' | 'moderate' | 'major' | 'critical'
  location: {
    notationIndex: number
    measure?: number
    beat?: number
  }
  expected: any
  actual: any
  description: string
  suggestion: string
  culturalContext?: string
}

export interface DetailedFeedback {
  overall: {
    score: number // 0-100
    grade: 'A' | 'B' | 'C' | 'D' | 'F'
    summary: string
    strengths: string[]
    areasForImprovement: string[]
  }
  technical: {
    pitchAccuracy: {
      score: number
      feedback: string
      specificNotes: {
        swara: SwaraName
        accuracy: number
        suggestion: string
      }[]
    }
    rhythmAccuracy: {
      score: number
      feedback: string
      timingAnalysis: {
        beat: number
        deviation: number
        suggestion: string
      }[]
    }
    gamakaExecution: {
      score: number
      feedback: string
      patterns: {
        type: string
        quality: number
        suggestion: string
      }[]
    }
  }
  cultural: {
    ragaAdherence: {
      score: number
      feedback: string
      suggestions: string[]
    }
    styleAuthenticity: {
      score: number
      feedback: string
      traditionalContext: string
    }
    expression: {
      score: number
      feedback: string
      emotionalContent: number
    }
  }
  nextSteps: {
    immediateActions: string[]
    practiceRecommendations: string[]
    progressionPath: string[]
    estimatedPracticeTime: number
  }
}

// Learning progress tracking
export interface ExerciseProgress {
  exerciseId: string
  userId: string
  currentLevel: number
  completionPercentage: number
  bestScore: number
  averageScore: number
  totalAttempts: number
  successfulAttempts: number
  totalPracticeTime: number
  lastPracticedAt: number
  masteryLevel: 'novice' | 'developing' | 'proficient' | 'advanced' | 'expert'
  skillBreakdown: {
    pitch: number // 0-1
    rhythm: number // 0-1
    expression: number // 0-1
    cultural: number // 0-1
  }
  learningCurve: {
    date: number
    score: number
    practiceTime: number
  }[]
  achievements: {
    id: string
    name: string
    description: string
    unlockedAt: number
  }[]
  nextMilestone: {
    description: string
    targetScore: number
    estimatedTime: number
    requirements: string[]
  }
}

export interface LearningPath {
  id: string
  name: string
  nameDevanagari: string
  description: string
  level: DifficultyLevel
  estimatedWeeks: number
  prerequisiteKnowledge: string[]
  learningOutcomes: string[]
  culturalBackground: string
  exercises: {
    exerciseId: string
    order: number
    isCore: boolean
    minScoreToProgress: number
    estimatedHours: number
    dependencies: string[]
  }[]
  assessments: {
    id: string
    name: string
    type: 'quiz' | 'practical' | 'performance'
    requiredScore: number
    exercises: string[]
  }[]
  certificates: {
    intermediate: {
      requirements: string[]
      template: string
    }
    completion: {
      requirements: string[]
      template: string
    }
  }
}

export interface UserLearningProfile {
  userId: string
  musicalBackground: 'none' | 'western' | 'hindustani' | 'carnatic' | 'folk' | 'mixed'
  experience: 'beginner' | 'someExperience' | 'intermediate' | 'advanced'
  goals: ('cultural' | 'performance' | 'teaching' | 'recreation' | 'spiritual')[]
  preferredLearningStyle: ('visual' | 'auditory' | 'kinesthetic' | 'reading')[]
  practiceSchedule: {
    frequency: number // sessions per week
    duration: number // minutes per session
    preferredTimes: string[]
    consistency: number // 0-1
  }
  strengths: string[]
  challengeAreas: string[]
  currentPath?: string
  completedPaths: string[]
  personalizedRecommendations: {
    nextExercises: string[]
    focusAreas: string[]
    practiceSchedule: string
    motivationalTips: string[]
  }
}

// Assessment and evaluation
export interface Assessment {
  id: string
  name: string
  type: 'diagnostic' | 'formative' | 'summative' | 'certification'
  exercises: string[]
  timeLimit?: number // minutes
  passingScore: number
  attempts: AssessmentAttempt[]
  rubric: {
    criteria: string
    levels: {
      score: number
      description: string
      indicators: string[]
    }[]
  }[]
}

export interface AssessmentAttempt {
  id: string
  assessmentId: string
  userId: string
  startTime: number
  endTime: number
  score: number
  passed: boolean
  performance: PerformanceAnalysis
  feedback: DetailedFeedback
  recommendations: string[]
  certificateAwarded?: string
}

// Gamification elements
export interface Achievement {
  id: string
  name: string
  nameDevanagari: string
  description: string
  category: 'practice' | 'skill' | 'cultural' | 'social' | 'milestone'
  difficulty: 'bronze' | 'silver' | 'gold' | 'platinum'
  icon: string
  requirements: {
    type: 'exercise_completion' | 'score_achievement' | 'streak_maintenance' | 'time_based' | 'cultural_knowledge'
    criteria: any
  }
  rewards: {
    points: number
    title?: string
    features?: string[]
  }
  cultural_significance?: string
}

export interface Badge {
  id: string
  achievementId: string
  userId: string
  awardedAt: number
  level: 'bronze' | 'silver' | 'gold' | 'platinum'
  progress?: {
    current: number
    target: number
    percentage: number
  }
}

// Teacher and mentor features
export interface TeacherProfile {
  id: string
  name: string
  credentials: string[]
  specializations: string[]
  experience: number // years
  teachingPhilosophy: string
  culturalLineage: string
  availableLanguages: string[]
  styles: string[]
  rating: number
  reviews: TeacherReview[]
}

export interface TeacherReview {
  id: string
  teacherId: string
  studentId: string
  rating: number
  feedback: string
  aspects: {
    knowledge: number
    patience: number
    culturalAuthenticity: number
    communication: number
  }
  createdAt: number
}

export interface Lesson {
  id: string
  teacherId?: string
  studentId: string
  type: 'individual' | 'group' | 'masterclass'
  status: 'scheduled' | 'ongoing' | 'completed' | 'cancelled'
  scheduledTime: number
  duration: number
  exercises: string[]
  goals: string[]
  notes: string
  recordings?: {
    audio?: string
    video?: string
    annotations: {
      timestamp: number
      note: string
      type: 'correction' | 'praise' | 'technique' | 'cultural'
    }[]
  }
  homework?: {
    exercises: string[]
    goals: string[]
    dueDate: number
  }
}

// Export utility types
export type ExerciseFilter = {
  type?: ExerciseType[]
  difficulty?: DifficultyLevel[]
  raga?: string[]
  level?: number[]
  duration?: [number, number] // min, max minutes
  tags?: string[]
  hasAudio?: boolean
  hasVideo?: boolean
  cultural?: string[]
}

export type ProgressMetric = 'accuracy' | 'consistency' | 'expression' | 'cultural' | 'overall'

export type FeedbackType = 'immediate' | 'session' | 'weekly' | 'monthly' | 'assessment'