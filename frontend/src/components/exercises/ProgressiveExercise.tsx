import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import SwaraWheel from '@/components/carnatic/SwaraWheel'
import { cn } from '@/utils/cn'

interface ExerciseLevel {
  id: number
  name: string
  description: string
  target_swaras: string[]
  tempo: number
  duration_seconds: number
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  requirements: {
    accuracy_threshold: number
    consistency_threshold: number
    min_attempts: number
  }
}

interface ExerciseProgress {
  level_id: number
  attempts: number
  best_accuracy: number
  best_consistency: number
  completed: boolean
  unlocked: boolean
}

interface ProgressiveExerciseProps {
  exerciseType: 'swara_practice' | 'sarali_varisai' | 'alankara'
  currentLevel?: number
  onLevelComplete: (levelId: number, score: ExerciseScore) => void
  onProgressUpdate: (progress: ExerciseProgress[]) => void
  className?: string
}

interface ExerciseScore {
  accuracy: number
  consistency: number
  tempo_stability: number
  overall: number
}

interface CurrentSession {
  level: ExerciseLevel
  startTime: number
  currentSwara: string
  targetSwara: string
  swaraIndex: number
  isRecording: boolean
  feedback: string[]
}

const ProgressiveExercise: React.FC<ProgressiveExerciseProps> = ({
  exerciseType,
  currentLevel = 1,
  onLevelComplete,
  onProgressUpdate,
  className
}) => {
  const [levels, setLevels] = useState<ExerciseLevel[]>([])
  const [progress, setProgress] = useState<ExerciseProgress[]>([])
  const [currentSession, setCurrentSession] = useState<CurrentSession | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [sessionScore, setSessionScore] = useState<ExerciseScore | null>(null)
  const [showLevelComplete, setShowLevelComplete] = useState(false)

  useEffect(() => {
    fetchExerciseLevels()
    fetchProgress()
  }, [exerciseType])

  useEffect(() => {
    if (currentSession && currentSession.isRecording) {
      const interval = setInterval(() => {
        // Simulate swara progression for demo
        setCurrentSession(prev => {
          if (!prev) return null

          const nextIndex = (prev.swaraIndex + 1) % prev.level.target_swaras.length
          return {
            ...prev,
            swaraIndex: nextIndex,
            targetSwara: prev.level.target_swaras[nextIndex]
          }
        })
      }, 60000 / (currentSession.level.tempo * 4)) // Quarter note timing

      return () => clearInterval(interval)
    }
  }, [currentSession?.isRecording, currentSession?.level.tempo])

  const fetchExerciseLevels = async () => {
    try {
      const response = await fetch(`/api/exercises/${exerciseType}/levels`)
      const data = await response.json()
      setLevels(data)
    } catch (error) {
      console.error('Failed to fetch exercise levels:', error)
      // Fallback data for demo
      setLevels(generateDemoLevels())
    }
  }

  const fetchProgress = async () => {
    try {
      const response = await fetch(`/api/exercises/${exerciseType}/progress`)
      const data = await response.json()
      setProgress(data)
    } catch (error) {
      console.error('Failed to fetch progress:', error)
      setProgress(generateInitialProgress())
    } finally {
      setIsLoading(false)
    }
  }

  const generateDemoLevels = (): ExerciseLevel[] => {
    const baseExercises = {
      swara_practice: [
        { swaras: ['Sa'], name: 'Sa Foundation', description: 'Master the fundamental Sa' },
        { swaras: ['Sa', 'Ri'], name: 'Sa-Ri Practice', description: 'Practice Sa to Ri transitions' },
        { swaras: ['Sa', 'Ri', 'Ga'], name: 'Lower Swaras', description: 'Master Sa-Ri-Ga progression' },
        { swaras: ['Sa', 'Ri', 'Ga', 'Ma'], name: 'First Tetrachord', description: 'Complete lower tetrachord' },
        { swaras: ['Sa', 'Ri', 'Ga', 'Ma', 'Pa'], name: 'Extended Range', description: 'Add Pa to your range' }
      ],
      sarali_varisai: [
        { swaras: ['Sa', 'Ri', 'Ga', 'Ma'], name: 'Basic Sarali 1', description: 'Simple ascending pattern' },
        { swaras: ['Sa', 'Ri', 'Ga', 'Ma', 'Pa'], name: 'Basic Sarali 2', description: 'Extended ascending' },
        { swaras: ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da'], name: 'Basic Sarali 3', description: 'Six note patterns' },
        { swaras: ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni'], name: 'Full Scale', description: 'Complete octave sarali' }
      ],
      alankara: [
        { swaras: ['Sa', 'Ri', 'Sa'], name: 'Simple Alankara 1', description: 'Basic three-note pattern' },
        { swaras: ['Sa', 'Ri', 'Ga', 'Ri'], name: 'Simple Alankara 2', description: 'Four-note returning pattern' },
        { swaras: ['Sa', 'Ri', 'Ga', 'Ma', 'Ga', 'Ri'], name: 'Complex Alankara 1', description: 'Six-note complex pattern' }
      ]
    }

    return baseExercises[exerciseType].map((ex, index) => ({
      id: index + 1,
      name: ex.name,
      description: ex.description,
      target_swaras: ex.swaras,
      tempo: 60 + (index * 10),
      duration_seconds: 120,
      difficulty: index < 2 ? 'beginner' : index < 4 ? 'intermediate' : 'advanced',
      requirements: {
        accuracy_threshold: 0.8 - (index * 0.05),
        consistency_threshold: 0.75,
        min_attempts: 3
      }
    }))
  }

  const generateInitialProgress = (): ExerciseProgress[] => {
    return levels.map((level, index) => ({
      level_id: level.id,
      attempts: 0,
      best_accuracy: 0,
      best_consistency: 0,
      completed: false,
      unlocked: index === 0 // Only first level unlocked initially
    }))
  }

  const startLevel = (level: ExerciseLevel) => {
    setCurrentSession({
      level,
      startTime: Date.now(),
      currentSwara: level.target_swaras[0],
      targetSwara: level.target_swaras[0],
      swaraIndex: 0,
      isRecording: false,
      feedback: []
    })
    setSessionScore(null)
    setShowLevelComplete(false)
  }

  const startRecording = () => {
    if (currentSession) {
      setCurrentSession(prev => prev ? { ...prev, isRecording: true } : null)
    }
  }

  const stopRecording = () => {
    if (currentSession) {
      setCurrentSession(prev => prev ? { ...prev, isRecording: false } : null)

      // Simulate scoring
      setTimeout(() => {
        const score: ExerciseScore = {
          accuracy: 0.75 + Math.random() * 0.2,
          consistency: 0.7 + Math.random() * 0.25,
          tempo_stability: 0.8 + Math.random() * 0.15,
          overall: 0
        }
        score.overall = (score.accuracy + score.consistency + score.tempo_stability) / 3

        setSessionScore(score)

        // Update progress
        const updatedProgress = progress.map(p => {
          if (p.level_id === currentSession.level.id) {
            const updated = {
              ...p,
              attempts: p.attempts + 1,
              best_accuracy: Math.max(p.best_accuracy, score.accuracy),
              best_consistency: Math.max(p.best_consistency, score.consistency)
            }

            // Check if level completed
            if (score.overall >= currentSession.level.requirements.accuracy_threshold &&
                updated.attempts >= currentSession.level.requirements.min_attempts) {
              updated.completed = true
              setShowLevelComplete(true)
              onLevelComplete(currentSession.level.id, score)
            }

            return updated
          }
          return p
        })

        // Unlock next level if current completed
        const currentIndex = updatedProgress.findIndex(p => p.level_id === currentSession.level.id)
        if (currentIndex !== -1 && updatedProgress[currentIndex].completed && currentIndex + 1 < updatedProgress.length) {
          updatedProgress[currentIndex + 1].unlocked = true
        }

        setProgress(updatedProgress)
        onProgressUpdate(updatedProgress)
      }, 2000)
    }
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'text-green-600 bg-green-100'
      case 'intermediate': return 'text-yellow-600 bg-yellow-100'
      case 'advanced': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  if (isLoading) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-6", className)}>
      {!currentSession ? (
        /* Level Selection */
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 capitalize">
              {exerciseType.replace('_', ' ')} Practice
            </h2>
            <p className="text-gray-600 mt-2">Choose your level and start practicing</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {levels.map((level, index) => {
              const levelProgress = progress.find(p => p.level_id === level.id)
              const isUnlocked = levelProgress?.unlocked || false
              const isCompleted = levelProgress?.completed || false

              return (
                <motion.div
                  key={level.id}
                  className={cn(
                    "p-6 rounded-lg border-2 transition-all duration-200",
                    isUnlocked
                      ? "border-gray-200 bg-white hover:border-orange-300 cursor-pointer"
                      : "border-gray-100 bg-gray-50 cursor-not-allowed opacity-60",
                    isCompleted && "border-green-300 bg-green-50"
                  )}
                  whileHover={isUnlocked ? { scale: 1.02 } : {}}
                  onClick={() => isUnlocked && startLevel(level)}
                >
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-bold text-gray-900">{level.name}</h3>
                      <div className="flex items-center space-x-2">
                        {isCompleted && (
                          <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                            <span className="text-white text-sm">✓</span>
                          </div>
                        )}
                        {!isUnlocked && (
                          <div className="w-6 h-6 bg-gray-400 rounded-full flex items-center justify-center">
                            <span className="text-white text-sm">🔒</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <p className="text-gray-600 text-sm">{level.description}</p>

                    <div className="flex items-center space-x-4 text-sm">
                      <span className={cn(
                        "px-2 py-1 rounded-full font-medium",
                        getDifficultyColor(level.difficulty)
                      )}>
                        {level.difficulty}
                      </span>
                      <span className="text-gray-500">{level.tempo} BPM</span>
                      <span className="text-gray-500">{level.duration_seconds}s</span>
                    </div>

                    <div className="text-sm text-gray-600">
                      <span className="font-medium">Target Swaras: </span>
                      {level.target_swaras.join(' - ')}
                    </div>

                    {levelProgress && levelProgress.attempts > 0 && (
                      <div className="text-sm space-y-1">
                        <div className="flex justify-between">
                          <span>Best Accuracy:</span>
                          <span>{Math.round(levelProgress.best_accuracy * 100)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Attempts:</span>
                          <span>{levelProgress.attempts}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      ) : (
        /* Practice Session */
        <div className="space-y-6">
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-bold text-gray-900">{currentSession.level.name}</h2>
            <p className="text-gray-600">{currentSession.level.description}</p>
            <div className="flex items-center justify-center space-x-4 text-sm">
              <span>Tempo: {currentSession.level.tempo} BPM</span>
              <span>•</span>
              <span>Target: {currentSession.targetSwara}</span>
            </div>
          </div>

          {/* Swara Wheel */}
          <div className="flex justify-center">
            <SwaraWheel
              currentSwara={currentSession.currentSwara}
              targetSwara={currentSession.targetSwara}
              confidence={0.8}
              centDeviation={Math.random() * 20 - 10}
              className="w-80 h-80"
            />
          </div>

          {/* Controls */}
          <div className="flex justify-center space-x-4">
            <Button
              variant={currentSession.isRecording ? "destructive" : "carnatic"}
              size="lg"
              onClick={currentSession.isRecording ? stopRecording : startRecording}
            >
              {currentSession.isRecording ? "Stop Recording" : "Start Recording"}
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => setCurrentSession(null)}
            >
              Back to Levels
            </Button>
          </div>

          {/* Score Display */}
          <AnimatePresence>
            {sessionScore && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-white p-6 rounded-lg border shadow-lg max-w-md mx-auto"
              >
                <h3 className="text-lg font-bold text-center mb-4">Session Results</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>Accuracy:</span>
                    <span className="font-medium">{Math.round(sessionScore.accuracy * 100)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Consistency:</span>
                    <span className="font-medium">{Math.round(sessionScore.consistency * 100)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tempo Stability:</span>
                    <span className="font-medium">{Math.round(sessionScore.tempo_stability * 100)}%</span>
                  </div>
                  <div className="border-t pt-3">
                    <div className="flex justify-between text-lg font-bold">
                      <span>Overall Score:</span>
                      <span className={cn(
                        sessionScore.overall >= 0.8 ? "text-green-600" :
                        sessionScore.overall >= 0.6 ? "text-yellow-600" : "text-red-600"
                      )}>
                        {Math.round(sessionScore.overall * 100)}%
                      </span>
                    </div>
                  </div>
                </div>

                {showLevelComplete && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="mt-4 p-3 bg-green-100 rounded-lg text-center"
                  >
                    <div className="text-green-800 font-bold">🎉 Level Complete!</div>
                    <div className="text-green-700 text-sm">Next level unlocked</div>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}

export default ProgressiveExercise