import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'
import {
  Play, Pause, RotateCcw, Volume2, VolumeX, Settings,
  ChevronLeft, ChevronRight, Award, Target, Timer
} from 'lucide-react'
import { RecordingInterface } from '@/components/audio/RecordingInterface'
import AudioVisualizer from '@/components/audio/AudioVisualizer'

interface JantaPattern {
  id: number
  name: string
  level: number
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  doubleNotes: Array<{
    first: string
    second: string
    duration: number
    emphasis: 'first' | 'second' | 'equal'
  }>
  tempo_range: [number, number]
  description: string
  culturalContext: string
  learningObjectives: string[]
  transitionFocus: string[]
  completionRequirements: {
    min_accuracy: number
    smooth_transitions: number
    min_sessions: number
    tempo_milestones: number[]
  }
}

interface JantaInterfaceProps {
  currentPattern?: JantaPattern
  onPatternSelect: (pattern: JantaPattern) => void
  onProgressUpdate: (progress: any) => void
  className?: string
}

interface PracticeState {
  isPlaying: boolean
  isPaused: boolean
  currentTempo: number
  currentNoteIndex: number
  practiceMode: 'listen' | 'practice' | 'assessment' | 'transition'
  accuracy: number
  transitionQuality: number
  completedCycles: number
  sessionTime: number
  focusArea: 'speed' | 'accuracy' | 'transitions' | 'all'
}

const JantaInterface: React.FC<JantaInterfaceProps> = ({
  currentPattern,
  onPatternSelect,
  onProgressUpdate,
  className
}) => {
  const [practiceState, setPracticeState] = useState<PracticeState>({
    isPlaying: false,
    isPaused: false,
    currentTempo: 60,
    currentNoteIndex: 0,
    practiceMode: 'listen',
    accuracy: 0,
    transitionQuality: 0,
    completedCycles: 0,
    sessionTime: 0,
    focusArea: 'all'
  })

  const [patterns, setPatterns] = useState<JantaPattern[]>([])
  const [showRecording, setShowRecording] = useState(false)
  const [volume, setVolume] = useState(0.7)
  const [isMuted, setIsMuted] = useState(false)
  const [transitionMetrics, setTransitionMetrics] = useState({
    smoothness: 0,
    timing: 0,
    pitch_accuracy: 0
  })

  const intervalRef = useRef<NodeJS.Timeout>()
  const audioContextRef = useRef<AudioContext>()
  const sessionStartRef = useRef<number>(Date.now())

  useEffect(() => {
    loadJantaPatterns()
    initializeAudio()
    return () => cleanup()
  }, [])

  useEffect(() => {
    if (practiceState.isPlaying && currentPattern) {
      startPracticeSequence()
    } else {
      stopPracticeSequence()
    }
  }, [practiceState.isPlaying, practiceState.currentTempo, currentPattern])

  const loadJantaPatterns = async () => {
    try {
      const response = await fetch('/api/exercises/janta/patterns')
      const data = await response.json()
      setPatterns(data)

      if (!currentPattern && data.length > 0) {
        onPatternSelect(data[0])
      }
    } catch (error) {
      console.error('Failed to load Janta patterns:', error)
      // Load demo patterns
      setPatterns(generateDemoPatterns())
    }
  }

  const generateDemoPatterns = (): JantaPattern[] => {
    return [
      {
        id: 1,
        name: "Janta Varisai 1",
        level: 1,
        difficulty: 'beginner',
        doubleNotes: [
          { first: 'Sa', second: 'Sa', duration: 1, emphasis: 'equal' },
          { first: 'Ri', second: 'Ri', duration: 1, emphasis: 'equal' },
          { first: 'Ga', second: 'Ga', duration: 1, emphasis: 'equal' },
          { first: 'Ma', second: 'Ma', duration: 1, emphasis: 'equal' }
        ],
        tempo_range: [40, 80],
        description: "Basic double-note pattern with equal emphasis",
        culturalContext: "Foundation for developing smooth note transitions in Carnatic music",
        learningObjectives: [
          "Master equal emphasis on repeated notes",
          "Develop smooth transition between different swaras",
          "Build consistency in note duration"
        ],
        transitionFocus: [
          "Sa-Sa to Ri-Ri connection",
          "Maintaining pitch accuracy in repetition",
          "Breath control for sustained doubles"
        ],
        completionRequirements: {
          min_accuracy: 0.85,
          smooth_transitions: 0.8,
          min_sessions: 5,
          tempo_milestones: [40, 60, 80]
        }
      },
      {
        id: 2,
        name: "Janta Varisai 2",
        level: 2,
        difficulty: 'beginner',
        doubleNotes: [
          { first: 'Sa', second: 'Sa', duration: 1, emphasis: 'equal' },
          { first: 'Ri', second: 'Ri', duration: 1, emphasis: 'equal' },
          { first: 'Sa', second: 'Sa', duration: 1, emphasis: 'equal' }
        ],
        tempo_range: [45, 90],
        description: "Return pattern with double notes",
        culturalContext: "Teaches direction changes while maintaining double-note clarity",
        learningObjectives: [
          "Master return movements in double-note context",
          "Develop phrase direction awareness",
          "Build confidence with pattern reversals"
        ],
        transitionFocus: [
          "Ri-Ri to Sa-Sa return transition",
          "Direction change smoothness",
          "Maintaining tempo through reversals"
        ],
        completionRequirements: {
          min_accuracy: 0.8,
          smooth_transitions: 0.75,
          min_sessions: 6,
          tempo_milestones: [45, 70, 90]
        }
      },
      {
        id: 3,
        name: "Janta Varisai 3",
        level: 3,
        difficulty: 'intermediate',
        doubleNotes: [
          { first: 'Sa', second: 'Sa', duration: 0.5, emphasis: 'first' },
          { first: 'Ri', second: 'Ri', duration: 1, emphasis: 'equal' },
          { first: 'Ga', second: 'Ga', duration: 1.5, emphasis: 'second' },
          { first: 'Ma', second: 'Ma', duration: 1, emphasis: 'equal' }
        ],
        tempo_range: [50, 110],
        description: "Variable duration and emphasis patterns",
        culturalContext: "Introduces rhythmic complexity and emphasis variation in janta exercises",
        learningObjectives: [
          "Master different emphasis patterns",
          "Develop rhythmic flexibility",
          "Control duration variations smoothly"
        ],
        transitionFocus: [
          "Variable emphasis transitions",
          "Duration change smoothness",
          "Maintaining melodic flow with rhythm changes"
        ],
        completionRequirements: {
          min_accuracy: 0.8,
          smooth_transitions: 0.85,
          min_sessions: 8,
          tempo_milestones: [50, 80, 110]
        }
      }
    ]
  }

  const initializeAudio = () => {
    try {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
    } catch (error) {
      console.error('Web Audio API not supported:', error)
    }
  }

  const cleanup = () => {
    stopPracticeSequence()
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }
  }

  const startPracticeSequence = () => {
    if (!currentPattern) return

    let noteIndex = 0
    const beatDuration = (60 / practiceState.currentTempo) * 1000

    intervalRef.current = setInterval(() => {
      const doubleNote = currentPattern.doubleNotes[noteIndex]

      // Play first note of the pair
      if (!isMuted) {
        playDoubleNote(doubleNote, 0)

        // Play second note after appropriate delay
        setTimeout(() => {
          playDoubleNote(doubleNote, 1)
        }, beatDuration * doubleNote.duration * 0.5)
      }

      setPracticeState(prev => ({
        ...prev,
        currentNoteIndex: noteIndex,
        sessionTime: (Date.now() - sessionStartRef.current) / 1000
      }))

      noteIndex = (noteIndex + 1) % currentPattern.doubleNotes.length

      if (noteIndex === 0) {
        setPracticeState(prev => ({
          ...prev,
          completedCycles: prev.completedCycles + 1
        }))
      }
    }, beatDuration)
  }

  const stopPracticeSequence = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = undefined
    }
  }

  const playDoubleNote = (doubleNote: JantaPattern['doubleNotes'][0], notePosition: 0 | 1) => {
    if (!audioContextRef.current) return

    const swaraFrequencies = {
      'Sa': 261.63, 'Ri': 293.66, 'Ga': 329.63, 'Ma': 349.23,
      'Pa': 392.00, 'Da': 440.00, 'Ni': 493.88
    }

    const swara = notePosition === 0 ? doubleNote.first : doubleNote.second
    const frequency = swaraFrequencies[swara as keyof typeof swaraFrequencies] || 261.63

    // Calculate emphasis-based volume
    let noteVolume = volume * 0.3
    if (doubleNote.emphasis === 'first' && notePosition === 0) {
      noteVolume *= 1.3
    } else if (doubleNote.emphasis === 'second' && notePosition === 1) {
      noteVolume *= 1.3
    }

    const duration = (60 / practiceState.currentTempo) * doubleNote.duration * 0.4

    const oscillator = audioContextRef.current.createOscillator()
    const gainNode = audioContextRef.current.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContextRef.current.destination)

    oscillator.frequency.setValueAtTime(frequency, audioContextRef.current.currentTime)
    oscillator.type = 'sine'

    gainNode.gain.setValueAtTime(0, audioContextRef.current.currentTime)
    gainNode.gain.linearRampToValueAtTime(noteVolume, audioContextRef.current.currentTime + 0.01)
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContextRef.current.currentTime + duration)

    oscillator.start(audioContextRef.current.currentTime)
    oscillator.stop(audioContextRef.current.currentTime + duration)
  }

  const handlePlayPause = () => {
    setPracticeState(prev => ({
      ...prev,
      isPlaying: !prev.isPlaying,
      isPaused: prev.isPlaying
    }))
  }

  const handleTempoChange = (newTempo: number) => {
    setPracticeState(prev => ({
      ...prev,
      currentTempo: Math.max(30, Math.min(200, newTempo))
    }))
  }

  const handleModeChange = (mode: PracticeState['practiceMode']) => {
    setPracticeState(prev => ({
      ...prev,
      practiceMode: mode,
      isPlaying: false
    }))
  }

  const handleFocusAreaChange = (area: PracticeState['focusArea']) => {
    setPracticeState(prev => ({
      ...prev,
      focusArea: area
    }))
  }

  const handleReset = () => {
    setPracticeState(prev => ({
      ...prev,
      isPlaying: false,
      currentNoteIndex: 0,
      completedCycles: 0,
      accuracy: 0,
      transitionQuality: 0,
      sessionTime: 0
    }))
    sessionStartRef.current = Date.now()
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'text-green-600 bg-green-100'
      case 'intermediate': return 'text-yellow-600 bg-yellow-100'
      case 'advanced': return 'text-orange-600 bg-orange-100'
      case 'expert': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  if (!currentPattern) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="text-gray-600">Loading Janta Varisai patterns...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">जंता वरिसै</h1>
        <h2 className="text-xl text-gray-700">Janta Varisai</h2>
        <p className="text-gray-600">Double Note Exercise Patterns</p>
      </div>

      {/* Pattern Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg border shadow-sm p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900">{currentPattern.name}</h3>
            <span className={cn(
              "inline-block px-2 py-1 rounded-full text-xs font-medium mt-2",
              getDifficultyColor(currentPattern.difficulty)
            )}>
              Level {currentPattern.level} - {currentPattern.difficulty}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowRecording(!showRecording)}
            >
              {showRecording ? 'Hide Recording' : 'Show Recording'}
            </Button>
          </div>
        </div>

        <p className="text-gray-700 mb-4">{currentPattern.description}</p>
        <p className="text-sm text-gray-600 mb-4 bg-blue-50 p-3 rounded-lg">
          <strong>Cultural Context:</strong> {currentPattern.culturalContext}
        </p>

        {/* Double Notes Pattern Display */}
        <div className="mb-6">
          <h4 className="font-semibold text-gray-800 mb-3">Double Note Pattern</h4>
          <div className="flex flex-wrap gap-3">
            {currentPattern.doubleNotes.map((doubleNote, index) => (
              <motion.div
                key={index}
                className={cn(
                  "flex items-center space-x-1 px-4 py-3 rounded-lg border-2 transition-all",
                  practiceState.currentNoteIndex === index && practiceState.isPlaying
                    ? "border-blue-400 bg-blue-100 scale-105"
                    : "border-gray-200 bg-gray-50"
                )}
                animate={
                  practiceState.currentNoteIndex === index && practiceState.isPlaying
                    ? { scale: [1, 1.05, 1], transition: { duration: 0.6 } }
                    : {}
                }
              >
                <div className={cn(
                  "px-3 py-1 rounded-full text-sm font-medium",
                  doubleNote.emphasis === 'first'
                    ? "bg-blue-200 text-blue-800"
                    : doubleNote.emphasis === 'equal'
                    ? "bg-gray-200 text-gray-800"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {doubleNote.first}
                </div>
                <span className="text-gray-400">+</span>
                <div className={cn(
                  "px-3 py-1 rounded-full text-sm font-medium",
                  doubleNote.emphasis === 'second'
                    ? "bg-blue-200 text-blue-800"
                    : doubleNote.emphasis === 'equal'
                    ? "bg-gray-200 text-gray-800"
                    : "bg-gray-100 text-gray-600"
                )}>
                  {doubleNote.second}
                </div>
                <div className="text-xs text-gray-500 ml-2">
                  {doubleNote.duration}x
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Recording Interface */}
      <AnimatePresence>
        {showRecording && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <RecordingInterface
              onRecordingComplete={(blob, analysis) => {
                console.log('Janta recording complete:', analysis)
              }}
              onPitchDetection={(freq, note, confidence) => {
                // Update transition metrics based on pitch detection
              }}
              className="mb-6"
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Practice Controls */}
      <div className="bg-white rounded-lg border shadow-sm p-6 space-y-6">
        {/* Mode and Focus Selection */}
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Practice Mode</label>
            <div className="flex flex-wrap gap-2">
              {(['listen', 'practice', 'assessment', 'transition'] as const).map((mode) => (
                <Button
                  key={mode}
                  variant={practiceState.practiceMode === mode ? "carnatic" : "outline"}
                  size="sm"
                  onClick={() => handleModeChange(mode)}
                  className="capitalize"
                >
                  {mode}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">Focus Area</label>
            <div className="flex flex-wrap gap-2">
              {(['speed', 'accuracy', 'transitions', 'all'] as const).map((area) => (
                <Button
                  key={area}
                  variant={practiceState.focusArea === area ? "carnatic" : "outline"}
                  size="sm"
                  onClick={() => handleFocusAreaChange(area)}
                  className="capitalize"
                >
                  {area}
                </Button>
              ))}
            </div>
          </div>
        </div>

        {/* Tempo Control */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">
            Tempo: {practiceState.currentTempo} BPM
          </label>
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleTempoChange(practiceState.currentTempo - 10)}
              disabled={practiceState.currentTempo <= 30}
            >
              -10
            </Button>
            <input
              type="range"
              min="30"
              max="200"
              value={practiceState.currentTempo}
              onChange={(e) => handleTempoChange(parseInt(e.target.value))}
              className="flex-1"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleTempoChange(practiceState.currentTempo + 10)}
              disabled={practiceState.currentTempo >= 200}
            >
              +10
            </Button>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center justify-center space-x-4">
          <Button
            variant={practiceState.isPlaying ? "destructive" : "carnatic"}
            size="lg"
            onClick={handlePlayPause}
            className="flex items-center space-x-2"
          >
            {practiceState.isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
            <span>{practiceState.isPlaying ? 'Pause' : 'Play Pattern'}</span>
          </Button>

          <Button
            variant="outline"
            size="lg"
            onClick={handleReset}
          >
            <RotateCcw className="h-5 w-5" />
          </Button>

          <Button
            variant="outline"
            size="lg"
            onClick={() => setIsMuted(!isMuted)}
          >
            {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
          </Button>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 pt-4 border-t">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{practiceState.completedCycles}</div>
            <div className="text-xs text-gray-600">Cycles</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{practiceState.accuracy.toFixed(1)}%</div>
            <div className="text-xs text-gray-600">Accuracy</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{practiceState.transitionQuality.toFixed(1)}%</div>
            <div className="text-xs text-gray-600">Transitions</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{practiceState.currentTempo}</div>
            <div className="text-xs text-gray-600">BPM</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-indigo-600">{formatTime(practiceState.sessionTime)}</div>
            <div className="text-xs text-gray-600">Time</div>
          </div>
        </div>
      </div>

      {/* Pattern Selection */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <h4 className="font-semibold text-gray-800 mb-4">Available Patterns</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {patterns.map((pattern) => (
            <motion.div
              key={pattern.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={cn(
                "p-4 rounded-lg border cursor-pointer transition-all",
                currentPattern.id === pattern.id
                  ? "border-blue-400 bg-blue-50"
                  : "border-gray-200 hover:border-blue-200 hover:bg-blue-25"
              )}
              onClick={() => onPatternSelect(pattern)}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h5 className="font-medium text-gray-900">{pattern.name}</h5>
                  <span className={cn(
                    "px-2 py-1 rounded-full text-xs font-medium",
                    getDifficultyColor(pattern.difficulty)
                  )}>
                    L{pattern.level}
                  </span>
                </div>
                <p className="text-sm text-gray-600 line-clamp-2">{pattern.description}</p>
                <div className="text-xs text-gray-500">
                  Tempo: {pattern.tempo_range[0]}-{pattern.tempo_range[1]} BPM
                </div>
                <div className="text-xs text-blue-600">
                  {pattern.doubleNotes.length} double-note pairs
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}

export { JantaInterface }