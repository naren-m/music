import React, { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import SwaraWheel from '@/components/carnatic/SwaraWheel'
import { cn } from '@/utils/cn'
import { Play, Pause, RotateCcw, Volume2, VolumeX, Settings, Mic, AlertCircle, ListOrdered, ChevronRight, Trophy, RefreshCw, X } from 'lucide-react'
import { useAudio, PracticeFeedback, SessionEventType, SessionExercise } from '../../../contexts/AudioContext'

interface SaraliPattern {
  id: number
  name: string
  level: number
  arohanam: string[]
  avarohanam: string[]
  tempo_range: [number, number]
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  description: string
  learning_objectives: string[]
  practice_tips: string[]
  completion_requirements: {
    min_accuracy: number
    min_sessions: number
    tempo_progression: number[]
  }
}

// Session Mode Types
interface SessionProgress {
  current_exercise_index: number
  total_exercises: number
  exercises_completed: number
  current_exercise_name: string
  is_current_completed: boolean
  session_active: boolean
}

interface ExerciseResult {
  index: number
  name: string
  total_notes: number
  correct: number
  incorrect: number
  accuracy: number
  grade: string
}

interface SessionSummary {
  total_exercises: number
  exercises_completed: number
  total_notes_played: number
  total_correct_notes: number
  total_incorrect_notes: number
  session_accuracy: number
  session_grade: string
  session_duration_seconds: number
  exercise_results: ExerciseResult[]
}

interface SessionState {
  isSessionMode: boolean
  sessionProgress: SessionProgress | null
  showCompletionModal: boolean
  showSessionSummary: boolean
  sessionSummary: SessionSummary | null
  currentExerciseResult: ExerciseResult | null
}

interface SaraliInterfaceProps {
  currentPattern?: SaraliPattern
  onPatternSelect: (pattern: SaraliPattern) => void
  onProgressUpdate: (progress: any) => void
  className?: string
}

interface PracticeState {
  isPlaying: boolean
  currentTempo: number
  swaraIndex: number
  accuracy: number
  completedCycles: number
}

const SaraliInterface: React.FC<SaraliInterfaceProps> = ({
  currentPattern,
  onPatternSelect,
  onProgressUpdate,
  className
}) => {
  const {
    currentPitch,
    stopPitchDetection,
    startRecording,
    stopRecording,
    isConnected,
    isRecording,
    startPracticeSession,
    stopPracticeSession,
    onPracticeFeedback,
    practiceProgress,
    // Session Mode
    startSessionMode,
    sessionRetryExercise,
    sessionNextExercise,
    sessionEnd,
    onSessionEvent,
  } = useAudio()

  const [practiceState, setPracticeState] = useState<PracticeState>({
    isPlaying: false,
    currentTempo: 60,
    swaraIndex: 0,
    accuracy: 0,
    completedCycles: 0
  })

  const [patterns, setPatterns] = useState<SaraliPattern[]>([])
  const [currentSwara, setCurrentSwara] = useState<string>('')
  const [targetSwara, setTargetSwara] = useState<string>('')
  const [showSettings, setShowSettings] = useState(false)
  const [volume, setVolume] = useState(0.7)
  const [isMuted, setIsMuted] = useState(false)
  const [feedbackMessage, setFeedbackMessage] = useState<string>('')
  const [serverFeedback, setServerFeedback] = useState<PracticeFeedback | null>(null)
  const [microphoneError, setMicrophoneError] = useState<string | null>(null)
  const [sessionStats, setSessionStats] = useState({
    startTime: Date.now(),
    totalTime: 0,
    accuracyHistory: [] as number[],
    mistakesCount: 0
  })

  // Session Mode State
  const [sessionState, setSessionState] = useState<SessionState>({
    isSessionMode: false,
    sessionProgress: null,
    showCompletionModal: false,
    showSessionSummary: false,
    sessionSummary: null,
    currentExerciseResult: null
  })

  const audioContextRef = useRef<AudioContext>()
  const socketRef = useRef<any>(null)

  // Base frequencies for validation
  const swaraFrequencies: Record<string, number> = {
    'Sa': 261.63,
    'Ri': 293.66,
    'Ga': 329.63,
    'Ma': 349.23,
    'Pa': 392.00,
    'Da': 440.00,
    'Ni': 493.88
  }

  useEffect(() => {
    loadSaraliPatterns()
    initializeAudio()
    return () => {
      if (audioContextRef.current) audioContextRef.current.close()
      stopPitchDetection()
    }
  }, [])

  // Subscribe to server practice feedback
  useEffect(() => {
    const unsubscribe = onPracticeFeedback((feedback: PracticeFeedback) => {
      setServerFeedback(feedback)

      // Update current detected swara
      if (feedback.shruti_name) {
        setCurrentSwara(feedback.shruti_name)
      }

      // Update feedback message based on validation
      if (feedback.validation) {
        if (feedback.validation.is_correct) {
          setFeedbackMessage(`✓ Correct! ${feedback.validation.expected_note}`)
          setSessionStats(prev => ({
            ...prev,
            accuracyHistory: [...prev.accuracyHistory, 100]
          }))
          if (feedback.validation.next_note) {
            setTargetSwara(feedback.validation.next_note)
          }
        } else {
          setFeedbackMessage(`Expected ${feedback.validation.expected_note}, heard ${feedback.validation.detected_note}`)
          setSessionStats(prev => ({
            ...prev,
            accuracyHistory: [...prev.accuracyHistory, 0],
            mistakesCount: prev.mistakesCount + 1
          }))
          if (feedback.validation.expected_note) {
            setTargetSwara(feedback.validation.expected_note)
          }
        }

        if (feedback.validation.progress) {
          setPracticeState(prev => ({
            ...prev,
            swaraIndex: feedback.validation!.progress.current,
            accuracy: feedback.validation!.progress.percentage
          }))
        }

        if (feedback.validation.completed) {
          setFeedbackMessage('🎉 Exercise Completed!')
          setPracticeState(prev => ({
            ...prev,
            isPlaying: false,
            completedCycles: prev.completedCycles + 1
          }))
        }
      }
    })

    return unsubscribe
  }, [onPracticeFeedback])

  // Subscribe to session mode events
  useEffect(() => {
    const unsubscribe = onSessionEvent((event: SessionEventType) => {
      console.log('Session event received:', event)

      switch (event.type) {
        case 'session_mode_started':
          setSessionState(prev => ({
            ...prev,
            isSessionMode: true,
            sessionProgress: {
              current_exercise_index: 0,
              total_exercises: event.data.total_exercises,
              exercises_completed: 0,
              current_exercise_name: event.data.current_exercise_name,
              is_current_completed: false,
              session_active: true,
            },
            showCompletionModal: false,
            showSessionSummary: false,
          }))
          // Sync currentPattern with the session's current exercise
          const startExercise = patterns.find(p => p.name === event.data.current_exercise_name)
          if (startExercise) {
            onPatternSelect(startExercise)
          }
          setTargetSwara(event.data.first_note)
          setPracticeState(prev => ({ ...prev, swaraIndex: 0 }))
          setFeedbackMessage(`🎤 Session started! Play ${event.data.first_note}`)
          break

        case 'exercise_completed':
          // Single exercise completed - show completion modal
          setSessionState(prev => ({
            ...prev,
            showCompletionModal: true,
          }))
          break

        case 'session_exercise_advanced':
          // Moved to next exercise
          setSessionState(prev => ({
            ...prev,
            sessionProgress: prev.sessionProgress ? {
              ...prev.sessionProgress,
              current_exercise_index: event.data.current_exercise_index,
              current_exercise_name: event.data.current_exercise_name,
              exercises_completed: event.data.current_exercise_index,
              is_current_completed: false,
            } : null,
            showCompletionModal: false,
            currentExerciseResult: event.data.previous_result || null,
          }))
          // Sync currentPattern with the new exercise
          const advancedExercise = patterns.find(p => p.name === event.data.current_exercise_name)
          if (advancedExercise) {
            onPatternSelect(advancedExercise)
          }
          setTargetSwara(event.data.first_note)
          setFeedbackMessage(`🎤 Next: ${event.data.current_exercise_name}. Play ${event.data.first_note}`)
          // Reset practice progress display
          setPracticeState(prev => ({
            ...prev,
            swaraIndex: 0,
            accuracy: 0,
          }))
          break

        case 'session_exercise_retried':
          // Exercise was retried
          setSessionState(prev => ({
            ...prev,
            showCompletionModal: false,
          }))
          // Ensure currentPattern is synced on retry
          const retriedExercise = patterns.find(p => p.name === event.data.current_exercise_name)
          if (retriedExercise) {
            onPatternSelect(retriedExercise)
          }
          setTargetSwara(event.data.first_note)
          setFeedbackMessage(`🔄 Retry! Play ${event.data.first_note}`)
          setPracticeState(prev => ({
            ...prev,
            swaraIndex: 0,
            accuracy: 0,
          }))
          break

        case 'session_completed':
        case 'session_ended':
          // Session is over - show summary
          setSessionState(prev => ({
            ...prev,
            isSessionMode: false,
            showCompletionModal: false,
            showSessionSummary: true,
            sessionSummary: event.data.summary,
            sessionProgress: null,
          }))
          setPracticeState(prev => ({
            ...prev,
            isPlaying: false,
          }))
          setFeedbackMessage('🎉 Session Complete!')
          break
      }
    })

    return unsubscribe
  }, [onSessionEvent, patterns, onPatternSelect])

  // Real-time pitch feedback from client-side detection (backup)
  useEffect(() => {
    if (!currentPitch || !targetSwara || !practiceState.isPlaying) {
      return
    }

    const targetFreq = swaraFrequencies[targetSwara]
    if (!targetFreq) return

    const deviation = 1200 * Math.log2(currentPitch.detectedFrequency / targetFreq)
    const absDeviation = Math.abs(deviation)

    if (absDeviation < 20) {
      setFeedbackMessage('Perfect! 🌟')
    } else if (absDeviation < 50) {
      setFeedbackMessage('Good')
    } else {
      setFeedbackMessage(deviation > 0 ? 'Too High ▼' : 'Too Low ▲')
    }
  }, [currentPitch, targetSwara, practiceState.isPlaying])

  const loadSaraliPatterns = async () => {
    try {
      const response = await fetch('/api/exercises/sarali/patterns')
      const data = await response.json()
      setPatterns(data)

      if (!currentPattern && data.length > 0) {
        onPatternSelect(data[0])
      }
    } catch (error) {
      console.error('Failed to load Sarali patterns:', error)
      setPatterns(generateDemoPatterns())
    }
  }

  const generateDemoPatterns = (): SaraliPattern[] => {
    return [
      {
        id: 1,
        name: "Sarali Varisai 1",
        level: 1,
        arohanam: ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni'],
        avarohanam: ['Ni', 'Da', 'Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
        tempo_range: [40, 80],
        difficulty: 'beginner',
        description: "Basic seven-note ascending and descending pattern",
        learning_objectives: [
          "Establish basic swara relationships",
          "Develop pitch accuracy for all seven swaras",
          "Learn fundamental ascending/descending movement"
        ],
        practice_tips: [
          "Start very slowly with metronome",
          "Focus on clean pitch transitions",
          "Sustain each swara clearly"
        ],
        completion_requirements: {
          min_accuracy: 0.8,
          min_sessions: 3,
          tempo_progression: [40, 60, 80]
        }
      },
      {
        id: 2,
        name: "Sarali Varisai 2",
        level: 2,
        arohanam: ['Sa', 'Ri', 'Ga', 'Ma', 'Pa'],
        avarohanam: ['Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
        tempo_range: [45, 90],
        difficulty: 'beginner',
        description: "Five-note pattern for beginners",
        learning_objectives: [
          "Master five-note movements",
          "Develop longer phrase control",
          "Improve breath management"
        ],
        practice_tips: [
          "Mark the turning point clearly",
          "Maintain consistent volume",
          "Practice hands to show direction"
        ],
        completion_requirements: {
          min_accuracy: 0.75,
          min_sessions: 4,
          tempo_progression: [45, 65, 90]
        }
      },
      {
        id: 3,
        name: "Sarali Varisai 3",
        level: 3,
        arohanam: ['Sa', 'Ri', 'Ga', 'Ma'],
        avarohanam: ['Ma', 'Ga', 'Ri', 'Sa'],
        tempo_range: [50, 100],
        difficulty: 'beginner',
        description: "Four-note basic pattern",
        learning_objectives: [
          "Focus on lower tetrachord",
          "Build foundation",
          "Develop stronger breath support"
        ],
        practice_tips: [
          "Practice Sa separately first",
          "Use hand gestures for pitch guidance",
          "Focus on smooth transitions"
        ],
        completion_requirements: {
          min_accuracy: 0.8,
          min_sessions: 5,
          tempo_progression: [50, 75, 100]
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

  const playSwara = (swara: string) => {
    if (!audioContextRef.current || isMuted) return

    const frequency = swaraFrequencies[swara] || 261.63
    const duration = (60 / practiceState.currentTempo) * 0.8

    const oscillator = audioContextRef.current.createOscillator()
    const gainNode = audioContextRef.current.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContextRef.current.destination)

    oscillator.frequency.setValueAtTime(frequency, audioContextRef.current.currentTime)
    oscillator.type = 'sine'

    gainNode.gain.setValueAtTime(0, audioContextRef.current.currentTime)
    gainNode.gain.linearRampToValueAtTime(volume * 0.3, audioContextRef.current.currentTime + 0.01)
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContextRef.current.currentTime + duration)

    oscillator.start(audioContextRef.current.currentTime)
    oscillator.stop(audioContextRef.current.currentTime + duration)
  }

  const handleStart = async () => {
    if (!currentPattern) return

    // Check WebSocket connection
    if (!isConnected) {
      setFeedbackMessage('Not connected to server. Please wait...')
      return
    }

    // Clear any previous errors
    setMicrophoneError(null)

    try {
      // Start recording first - this requests microphone permission
      await startRecording()

      // Build the full sequence (always use both arohanam and avarohanam)
      const fullSequence = [...currentPattern.arohanam, ...currentPattern.avarohanam]

      // Start the practice session on server
      startPracticeSession({
        pattern_name: currentPattern.name,
        arohanam: currentPattern.arohanam,
        avarohanam: currentPattern.avarohanam,
        include_avarohanam: true,
      })

      // Set target to first note
      if (fullSequence.length > 0) {
        setTargetSwara(fullSequence[0])
      }

      setFeedbackMessage(`🎤 Listening... Play ${fullSequence[0]}`)

      setPracticeState(prev => ({
        ...prev,
        isPlaying: true,
        swaraIndex: 0
      }))

    } catch (error) {
      console.error('Failed to start practice:', error)
      setMicrophoneError('Microphone access denied. Please allow microphone access and refresh the page.')
      setFeedbackMessage('Microphone access required')
    }
  }

  const handleStop = () => {
    stopPracticeSession()
    stopRecording()

    setPracticeState(prev => ({
      ...prev,
      isPlaying: false
    }))
    setFeedbackMessage('')
  }

  const handlePlayPause = () => {
    if (practiceState.isPlaying) {
      handleStop()
    } else {
      handleStart()
    }
  }

  const handleTempoChange = (newTempo: number) => {
    setPracticeState(prev => ({
      ...prev,
      currentTempo: Math.max(40, Math.min(200, newTempo))
    }))
  }

  const handleReset = () => {
    handleStop()
    setPracticeState(prev => ({
      ...prev,
      swaraIndex: 0,
      completedCycles: 0,
      accuracy: 0
    }))
    setCurrentSwara('')
    setTargetSwara('')
    setFeedbackMessage('')
    setMicrophoneError(null)
    setSessionStats({
      startTime: Date.now(),
      totalTime: 0,
      accuracyHistory: [],
      mistakesCount: 0
    })
  }

  // Session Mode Handlers
  const handleStartSession = async () => {
    if (!isConnected || patterns.length === 0) {
      setFeedbackMessage('Not ready to start session')
      return
    }

    setMicrophoneError(null)

    try {
      // Start recording first
      await startRecording()

      // Convert patterns to SessionExercise format
      const exercises: SessionExercise[] = patterns.map(p => ({
        name: p.name,
        arohanam: p.arohanam,
        avarohanam: p.avarohanam,
      }))

      // Set up initial pattern and target swara immediately (like single exercise mode)
      // This ensures UI is ready before audio streaming starts
      const firstPattern = patterns[0]
      if (firstPattern) {
        onPatternSelect(firstPattern)
        const firstNote = firstPattern.arohanam[0]
        setTargetSwara(firstNote)
        setFeedbackMessage(`🎤 Listening... Play ${firstNote}`)
      }

      // Start session mode
      startSessionMode(exercises)

      setPracticeState(prev => ({
        ...prev,
        isPlaying: true,
        swaraIndex: 0,
      }))
    } catch (error) {
      console.error('Failed to start session:', error)
      setMicrophoneError('Microphone access denied. Please allow microphone access.')
    }
  }

  const handleSessionRetry = () => {
    sessionRetryExercise()
    setSessionState(prev => ({
      ...prev,
      showCompletionModal: false,
    }))
  }

  const handleSessionNext = () => {
    sessionNextExercise()
    setSessionState(prev => ({
      ...prev,
      showCompletionModal: false,
    }))
  }

  const handleEndSession = () => {
    sessionEnd()
    stopRecording()
    setSessionState(prev => ({
      ...prev,
      isSessionMode: false,
      showCompletionModal: false,
      sessionProgress: null,
    }))
    setPracticeState(prev => ({
      ...prev,
      isPlaying: false,
    }))
  }

  const handleCloseSessionSummary = () => {
    setSessionState(prev => ({
      ...prev,
      showSessionSummary: false,
      sessionSummary: null,
    }))
  }

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getGradeColor = (grade: string): string => {
    switch (grade) {
      case 'A+': case 'A': return 'text-green-600 bg-green-100'
      case 'B+': case 'B': return 'text-blue-600 bg-blue-100'
      case 'C+': case 'C': return 'text-yellow-600 bg-yellow-100'
      case 'D': return 'text-orange-600 bg-orange-100'
      default: return 'text-red-600 bg-red-100'
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

  if (!currentPattern) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto"></div>
          <p className="text-gray-600">Loading Sarali Varisai patterns...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">सरली वरिसै</h1>
        <h2 className="text-xl text-gray-700">Sarali Varisai</h2>
        <p className="text-gray-600">Traditional Carnatic Music Exercise Patterns</p>
      </div>

      {/* Session Mode Progress Bar */}
      {sessionState.isSessionMode && sessionState.sessionProgress && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200 p-4"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <ListOrdered className="h-5 w-5 text-purple-600" />
              <span className="font-semibold text-purple-800">Session Mode</span>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleEndSession}
              className="text-red-600 border-red-200 hover:bg-red-50"
            >
              <X className="h-4 w-4 mr-1" />
              End Session
            </Button>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-purple-700 font-medium">
                {sessionState.sessionProgress.current_exercise_name}
              </span>
              <span className="text-purple-600">
                Exercise {sessionState.sessionProgress.current_exercise_index + 1} of {sessionState.sessionProgress.total_exercises}
              </span>
            </div>
            <div className="w-full bg-purple-100 rounded-full h-2.5">
              <div
                className="bg-gradient-to-r from-purple-500 to-indigo-500 h-2.5 rounded-full transition-all duration-500"
                style={{
                  width: `${((sessionState.sessionProgress.current_exercise_index) / sessionState.sessionProgress.total_exercises) * 100}%`
                }}
              />
            </div>
            <div className="flex justify-between text-xs text-purple-600">
              <span>{sessionState.sessionProgress.exercises_completed} completed</span>
              <span>{sessionState.sessionProgress.total_exercises - sessionState.sessionProgress.exercises_completed} remaining</span>
            </div>
          </div>
        </motion.div>
      )}

      {/* Microphone Error Alert */}
      {microphoneError && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3"
        >
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-red-800 font-medium">Microphone Access Required</p>
            <p className="text-red-600 text-sm mt-1">{microphoneError}</p>
          </div>
        </motion.div>
      )}

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
          <Button
            variant="outline"
            size="icon"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>

        <p className="text-gray-700 mb-4">{currentPattern.description}</p>

        {/* Pattern Display - Simplified to show full sequence */}
        <div className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-semibold text-gray-800">Practice Sequence</h4>
            <div className="flex flex-wrap gap-2">
              {[...currentPattern.arohanam, ...currentPattern.avarohanam].map((swara, index) => (
                <motion.span
                  key={`swara-${index}`}
                  className={cn(
                    "px-3 py-1 rounded-full border text-sm font-medium transition-all",
                    practiceState.swaraIndex === index && practiceState.isPlaying
                      ? "bg-orange-100 border-orange-400 text-orange-800 scale-110"
                      : targetSwara === swara
                      ? "bg-green-50 border-green-300 text-green-700"
                      : "bg-gray-50 border-gray-200 text-gray-700"
                  )}
                  animate={
                    practiceState.swaraIndex === index && practiceState.isPlaying
                      ? { scale: [1, 1.1, 1], transition: { duration: 0.3 } }
                      : {}
                  }
                >
                  {swara}
                </motion.span>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Swara Wheel */}
      <div className="flex flex-col items-center justify-center space-y-4">
        <SwaraWheel
          currentSwara={currentPitch?.shrutiName || currentPitch?.shruti?.name || currentSwara}
          targetSwara={targetSwara}
          confidence={currentPitch?.confidence || 0}
          centDeviation={currentPitch?.centDeviation || 0}
          className="w-80 h-80"
        />

        {/* Connection Status */}
        {!isConnected && (
          <motion.div
            key="connection-warning"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="px-4 py-2 rounded-full bg-red-100 text-red-700 font-medium"
          >
            Not connected to server. Please wait...
          </motion.div>
        )}

        {/* Feedback Message */}
        <AnimatePresence>
          {feedbackMessage && (
            <motion.div
              key="feedback-message"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className={cn(
                "px-4 py-2 rounded-full font-bold text-lg",
                feedbackMessage.includes('Perfect') || feedbackMessage.includes('Correct') || feedbackMessage.includes('✓')
                  ? "bg-green-100 text-green-700"
                  : feedbackMessage.includes('Good')
                  ? "bg-blue-100 text-blue-700"
                  : feedbackMessage.includes('Completed')
                  ? "bg-purple-100 text-purple-700"
                  : feedbackMessage.includes('Listening')
                  ? "bg-orange-100 text-orange-700"
                  : "bg-red-100 text-red-700"
              )}
            >
              {feedbackMessage}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Simplified Controls */}
      <div className="bg-white rounded-lg border shadow-sm p-6 space-y-4">
        {/* Connection & Recording Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className={cn(
                "w-3 h-3 rounded-full",
                isConnected ? "bg-green-500" : "bg-red-500"
              )} />
              <span className="text-sm text-gray-600">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            {isRecording && (
              <div className="flex items-center space-x-2 text-orange-600">
                <Mic className="h-4 w-4 animate-pulse" />
                <span className="text-sm font-medium">Recording</span>
              </div>
            )}
          </div>
        </div>

        {/* Progress Display */}
        {practiceProgress && practiceState.isPlaying && (
          <div className="bg-orange-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Exercise Progress</span>
              <span className="text-sm text-orange-600 font-bold">
                {practiceProgress.current} / {practiceProgress.total}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${practiceProgress.percentage}%` }}
              />
            </div>
            {serverFeedback?.expected_note && (
              <div className="mt-2 text-center">
                <span className="text-sm text-gray-600">Next note: </span>
                <span className="text-lg font-bold text-orange-700">
                  {serverFeedback.expected_note}
                </span>
              </div>
            )}
          </div>
        )}

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
              disabled={practiceState.currentTempo <= 40}
            >
              -10
            </Button>
            <input
              type="range"
              min="40"
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

        {/* Main Control Buttons */}
        <div className="flex items-center justify-center space-x-4">
          {/* Single Exercise Mode */}
          {!sessionState.isSessionMode && (
            <>
              <Button
                variant={practiceState.isPlaying ? "destructive" : "carnatic"}
                size="lg"
                onClick={handlePlayPause}
                disabled={!isConnected}
                className="flex items-center space-x-2 min-w-32"
              >
                {practiceState.isPlaying ? (
                  <>
                    <Pause className="h-5 w-5" />
                    <span>Stop</span>
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5" />
                    <span>Start</span>
                  </>
                )}
              </Button>

              {/* Start Session Button */}
              <Button
                variant="outline"
                size="lg"
                onClick={handleStartSession}
                disabled={!isConnected || practiceState.isPlaying || patterns.length === 0}
                className="flex items-center space-x-2 border-purple-300 text-purple-700 hover:bg-purple-50"
              >
                <ListOrdered className="h-5 w-5" />
                <span>Session</span>
              </Button>
            </>
          )}

          {/* Session Mode Controls */}
          {sessionState.isSessionMode && (
            <Button
              variant="destructive"
              size="lg"
              onClick={handleEndSession}
              className="flex items-center space-x-2"
            >
              <X className="h-5 w-5" />
              <span>End Session</span>
            </Button>
          )}

          <Button
            variant="outline"
            size="lg"
            onClick={handleReset}
            disabled={sessionState.isSessionMode}
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

        {/* Progress Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{practiceState.completedCycles}</div>
            <div className="text-xs text-gray-600">Cycles</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{practiceState.accuracy.toFixed(1)}%</div>
            <div className="text-xs text-gray-600">Accuracy</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{practiceState.currentTempo}</div>
            <div className="text-xs text-gray-600">BPM</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{Math.floor((Date.now() - sessionStats.startTime) / 60000)}</div>
            <div className="text-xs text-gray-600">Minutes</div>
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
                  ? "border-orange-400 bg-orange-50"
                  : "border-gray-200 hover:border-orange-200 hover:bg-orange-25"
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
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Settings Modal */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            key="settings-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setShowSettings(false)}
          >
            <motion.div
              key="settings-modal"
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-lg p-6 m-4 max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold mb-4">Practice Settings</h3>

              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700 block mb-2">
                    Volume: {Math.round(volume * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={volume}
                    onChange={(e) => setVolume(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>

                <div className="pt-4 border-t">
                  <h4 className="font-medium text-gray-800 mb-2">Learning Objectives</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {currentPattern.learning_objectives.map((objective, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-orange-500 mr-2">•</span>
                        {objective}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-4 border-t">
                  <h4 className="font-medium text-gray-800 mb-2">Practice Tips</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    {currentPattern.practice_tips.map((tip, index) => (
                      <li key={index} className="flex items-start">
                        <span className="text-green-500 mr-2">💡</span>
                        {tip}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="flex justify-end mt-6">
                <Button onClick={() => setShowSettings(false)}>Close</Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Exercise Completion Modal */}
      <AnimatePresence>
        {sessionState.showCompletionModal && sessionState.isSessionMode && (
          <motion.div
            key="completion-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          >
            <motion.div
              key="completion-modal"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-xl p-6 m-4 max-w-md w-full shadow-2xl"
            >
              <div className="text-center space-y-4">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                  <Trophy className="h-8 w-8 text-green-600" />
                </div>

                <h3 className="text-xl font-bold text-gray-900">
                  Exercise Complete! 🎉
                </h3>

                {sessionState.sessionProgress && (
                  <p className="text-gray-600">
                    You finished {sessionState.sessionProgress.current_exercise_name}
                  </p>
                )}

                {serverFeedback?.validation?.final_score && (
                  <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Accuracy</span>
                      <span className={cn(
                        "font-bold",
                        serverFeedback.validation.final_score.accuracy_percentage >= 80 ? "text-green-600" :
                        serverFeedback.validation.final_score.accuracy_percentage >= 60 ? "text-yellow-600" : "text-red-600"
                      )}>
                        {serverFeedback.validation.final_score.accuracy_percentage.toFixed(1)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Grade</span>
                      <span className={cn(
                        "px-2 py-0.5 rounded font-bold",
                        getGradeColor(serverFeedback.validation.final_score.grade)
                      )}>
                        {serverFeedback.validation.final_score.grade}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">
                        {serverFeedback.validation.final_score.correct} correct
                      </span>
                      <span className="text-gray-500">
                        {serverFeedback.validation.final_score.incorrect} incorrect
                      </span>
                    </div>
                  </div>
                )}

                <p className="text-sm text-gray-500">
                  What would you like to do next?
                </p>

                <div className="flex space-x-3">
                  <Button
                    variant="outline"
                    onClick={handleSessionRetry}
                    className="flex-1 flex items-center justify-center space-x-2"
                  >
                    <RefreshCw className="h-4 w-4" />
                    <span>Retry</span>
                  </Button>
                  <Button
                    variant="carnatic"
                    onClick={handleSessionNext}
                    className="flex-1 flex items-center justify-center space-x-2"
                  >
                    <span>Next Exercise</span>
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>

                <button
                  onClick={handleEndSession}
                  className="text-sm text-gray-500 hover:text-gray-700 underline"
                >
                  End Session Early
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Session Summary Modal */}
      <AnimatePresence>
        {sessionState.showSessionSummary && sessionState.sessionSummary && (
          <motion.div
            key="summary-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto"
          >
            <motion.div
              key="summary-modal"
              initial={{ scale: 0.9, opacity: 0, y: 20 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 20 }}
              className="bg-white rounded-xl p-6 m-4 max-w-lg w-full shadow-2xl my-8"
            >
              <div className="space-y-6">
                {/* Header */}
                <div className="text-center">
                  <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Trophy className="h-10 w-10 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900">Session Complete!</h2>
                  <p className="text-gray-600 mt-1">
                    Great practice session! Here's your summary.
                  </p>
                </div>

                {/* Overall Stats */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-purple-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-purple-600">
                      {sessionState.sessionSummary.exercises_completed}
                    </div>
                    <div className="text-sm text-purple-700">Exercises</div>
                  </div>
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {sessionState.sessionSummary.session_accuracy.toFixed(1)}%
                    </div>
                    <div className="text-sm text-green-700">Accuracy</div>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {sessionState.sessionSummary.total_notes_played}
                    </div>
                    <div className="text-sm text-blue-700">Notes Played</div>
                  </div>
                  <div className="bg-orange-50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-orange-600">
                      {formatDuration(sessionState.sessionSummary.session_duration_seconds)}
                    </div>
                    <div className="text-sm text-orange-700">Duration</div>
                  </div>
                </div>

                {/* Grade Badge */}
                <div className="flex justify-center">
                  <div className={cn(
                    "px-6 py-3 rounded-full text-2xl font-bold",
                    getGradeColor(sessionState.sessionSummary.session_grade)
                  )}>
                    Grade: {sessionState.sessionSummary.session_grade}
                  </div>
                </div>

                {/* Exercise Breakdown */}
                {sessionState.sessionSummary.exercise_results.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-800 mb-3">Exercise Breakdown</h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {sessionState.sessionSummary.exercise_results.map((result, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-2"
                        >
                          <span className="text-gray-700 text-sm">{result.name}</span>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-600">
                              {result.accuracy.toFixed(0)}%
                            </span>
                            <span className={cn(
                              "px-2 py-0.5 rounded text-xs font-bold",
                              getGradeColor(result.grade)
                            )}>
                              {result.grade}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex space-x-3">
                  <Button
                    variant="outline"
                    onClick={handleCloseSessionSummary}
                    className="flex-1"
                  >
                    Close
                  </Button>
                  <Button
                    variant="carnatic"
                    onClick={() => {
                      handleCloseSessionSummary()
                      handleStartSession()
                    }}
                    className="flex-1"
                  >
                    Start New Session
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export { SaraliInterface }
