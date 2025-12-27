import React, { useState, useCallback } from 'react'
import { SaraliInterface } from '../../components/exercises/sarali/SaraliInterface'

interface SaraliPattern {
  id?: number
  level: number
  name: string
  arohanam: string[] | { swara_sequence: string[] }
  avarohanam: string[] | { swara_sequence: string[] }
  tempo_range?: [number, number]
  difficulty?: 'beginner' | 'intermediate' | 'advanced'
  description?: string
  learning_objectives?: string[]
  practice_tips?: string[]
  completion_requirements?: {
    min_accuracy: number
    min_sessions: number
    tempo_progression: number[]
  }
}

const SaraliExercisePage: React.FC = () => {
  const [currentPattern, setCurrentPattern] = useState<SaraliPattern | undefined>(undefined)
  const [progress, setProgress] = useState<any>({})

  const handlePatternSelect = useCallback((pattern: SaraliPattern) => {
    // Transform API response to expected format if needed
    const transformedPattern: SaraliPattern = {
      id: pattern.level,
      level: pattern.level,
      name: pattern.name,
      arohanam: Array.isArray(pattern.arohanam)
        ? pattern.arohanam
        : (pattern.arohanam as any).swara_sequence || [],
      avarohanam: Array.isArray(pattern.avarohanam)
        ? pattern.avarohanam
        : (pattern.avarohanam as any).swara_sequence || [],
      tempo_range: pattern.tempo_range || [60, 120],
      difficulty: pattern.level <= 4 ? 'beginner' : pattern.level <= 8 ? 'intermediate' : 'advanced',
      description: pattern.description || '',
      learning_objectives: pattern.learning_objectives || [],
      practice_tips: pattern.practice_tips || [],
      completion_requirements: pattern.completion_requirements || {
        min_accuracy: 80,
        min_sessions: 3,
        tempo_progression: [60, 80, 100, 120]
      }
    }
    setCurrentPattern(transformedPattern)
  }, [])

  const handleProgressUpdate = useCallback((newProgress: any) => {
    setProgress((prev: any) => ({ ...prev, ...newProgress }))
  }, [])

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="carnatic-card p-6">
        <h1 className="text-3xl font-bold text-saffron-400 mb-2">
          Sarali Varisai • सरळी वरिसै
        </h1>
        <p className="text-gray-300 text-lg mb-4">
          Foundation exercises with ascending and descending melodic patterns
        </p>

        {/* Cultural Context */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h3 className="font-semibold text-white mb-2">Cultural Significance</h3>
          <p className="text-gray-400 text-sm">
            Sarali Varisai are the foundation exercises in Carnatic music education.
            They develop basic melodic movement, pitch accuracy, and rhythmic stability.
            The word "Sarali" means simple or straight, indicating the direct movement through the scale.
            These exercises prepare students for more complex ornamental patterns.
          </p>
        </div>
      </div>

      {/* Exercise Interface */}
      <div className="carnatic-card">
        <SaraliInterface
          currentPattern={currentPattern as any}
          onPatternSelect={handlePatternSelect as any}
          onProgressUpdate={handleProgressUpdate}
        />
      </div>

      {/* Practice Tips */}
      <div className="carnatic-card p-6">
        <h3 className="text-xl font-semibold text-white mb-4">Practice Tips</h3>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-saffron-400 mb-2">Technique Focus:</h4>
            <ul className="space-y-1 text-gray-400 text-sm">
              <li>• Maintain steady tempo throughout</li>
              <li>• Practice clear pronunciation of swaras</li>
              <li>• Focus on smooth voice transitions</li>
              <li>• Keep consistent breath support</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-saffron-400 mb-2">Progression Path:</h4>
            <ul className="space-y-1 text-gray-400 text-sm">
              <li>• Start with Level 1 (basic patterns)</li>
              <li>• Master accuracy before increasing tempo</li>
              <li>• Progress through all 12 levels systematically</li>
              <li>• Record sessions to track improvement</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SaraliExercisePage