import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import SwaraWheel from '@/components/carnatic/SwaraWheel'
import TalaVisualizer from '@/components/carnatic/TalaVisualizer'
import { cn } from '@/utils/cn'
import { Play, Pause, RotateCcw, Volume2, VolumeX, Settings } from 'lucide-react'

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

interface SaraliInterfaceProps {
  currentPattern?: SaraliPattern
  onPatternSelect: (pattern: SaraliPattern) => void
  onProgressUpdate: (progress: any) => void
  className?: string
}

interface PracticeState {
  isPlaying: boolean
  currentTempo: number
  currentSequence: 'arohanam' | 'avarohanam' | 'both'
  swaraIndex: number
  practiceMode: 'listen' | 'practice' | 'assessment'
  accuracy: number
  completedCycles: number
}

const SaraliInterface: React.FC<SaraliInterfaceProps> = ({
  currentPattern,
  onPatternSelect,
  onProgressUpdate,
  className
}) => {
  const [practiceState, setPracticeState] = useState<PracticeState>({
    isPlaying: false,
    currentTempo: 60,
    currentSequence: 'arohanam',
    swaraIndex: 0,
    practiceMode: 'listen',
    accuracy: 0,
    completedCycles: 0
  })

  const [patterns, setPatterns] = useState<SaraliPattern[]>([])
  const [currentSwara, setCurrentSwara] = useState<string>('')
  const [targetSwara, setTargetSwara] = useState<string>('')
  const [showSettings, setShowSettings] = useState(false)
  const [volume, setVolume] = useState(0.7)
  const [isMuted, setIsMuted] = useState(false)
  const [sessionStats, setSessionStats] = useState({
    startTime: Date.now(),
    totalTime: 0,
    accuracyHistory: [] as number[],
    mistakesCount: 0
  })

  const intervalRef = useRef<NodeJS.Timeout>()
  const audioContextRef = useRef<AudioContext>()

  useEffect(() => {
    loadSaraliPatterns()
    initializeAudio()
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
      if (audioContextRef.current) audioContextRef.current.close()
    }
  }, [])

  useEffect(() => {
    if (practiceState.isPlaying && currentPattern) {
      startPracticeSequence()
    } else {
      stopPracticeSequence()
    }
    return () => stopPracticeSequence()
  }, [practiceState.isPlaying, practiceState.currentTempo, currentPattern])

  const loadSaraliPatterns = async () => {
    try {
      const response = await fetch('/api/exercises/sarali/patterns')
      const data = await response.json()
      setPatterns(data)

      // If no pattern selected, select the first one
      if (!currentPattern && data.length > 0) {
        onPatternSelect(data[0])
      }
    } catch (error) {
      console.error('Failed to load Sarali patterns:', error)
      // Load demo patterns
      setPatterns(generateDemoPatterns())
    }
  }

  const generateDemoPatterns = (): SaraliPattern[] => {
    return [
      {
        id: 1,
        name: "Sarali Varisai 1",
        level: 1,
        arohanam: ['Sa', 'Ri', 'Ga', 'Ma'],
        avarohanam: ['Ma', 'Ga', 'Ri', 'Sa'],
        tempo_range: [40, 80],
        difficulty: 'beginner',
        description: "Basic four-note ascending and descending pattern",
        learning_objectives: [
          "Establish basic swara relationships",
          "Develop pitch accuracy for Sa-Ri-Ga-Ma",
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
        arohanam: ['Sa', 'Ri', 'Ga', 'Ma', 'Ma', 'Ga', 'Ri', 'Sa'],
        avarohanam: ['Sa', 'Ri', 'Ga', 'Ma', 'Ma', 'Ga', 'Ri', 'Sa'],
        tempo_range: [45, 90],
        difficulty: 'beginner',
        description: "Ascending and immediate return pattern",
        learning_objectives: [
          "Master return movements",
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
        arohanam: ['Sa', 'Ri', 'Ga', 'Ma', 'Pa'],
        avarohanam: ['Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
        tempo_range: [50, 100],
        difficulty: 'intermediate',
        description: "Five-note pattern including Pa",
        learning_objectives: [
          "Introduce Pa (fifth degree)",
          "Extend vocal range",
          "Develop stronger breath support"
        ],
        practice_tips: [
          "Practice Pa separately first",
          "Use hand gestures for pitch guidance",
          "Focus on smooth Ma-Pa transition"
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

  const startPracticeSequence = () => {
    if (!currentPattern) return

    const sequence = practiceState.currentSequence === 'arohanam'
      ? currentPattern.arohanam
      : practiceState.currentSequence === 'avarohanam'
      ? currentPattern.avarohanam
      : [...currentPattern.arohanam, ...currentPattern.avarohanam.slice(1).reverse()]

    let index = 0
    const beatDuration = (60 / practiceState.currentTempo) * 1000

    intervalRef.current = setInterval(() => {
      const swara = sequence[index]
      setCurrentSwara(swara)
      setTargetSwara(swara)

      // Play audio tone for the swara
      if (!isMuted) {
        playSwara(swara)
      }

      // Update practice state
      setPracticeState(prev => ({
        ...prev,
        swaraIndex: index
      }))

      index = (index + 1) % sequence.length

      if (index === 0) {
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

  const playSwara = (swara: string) => {
    if (!audioContextRef.current) return

    const swaraFrequencies = {
      'Sa': 261.63,   // C4
      'Ri': 293.66,   // D4
      'Ga': 329.63,   // E4
      'Ma': 349.23,   // F4
      'Pa': 392.00,   // G4
      'Da': 440.00,   // A4
      'Ni': 493.88    // B4
    }

    const frequency = swaraFrequencies[swara as keyof typeof swaraFrequencies] || 261.63
    const duration = (60 / practiceState.currentTempo) * 0.8 // 80% of beat duration

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

  const handlePlayPause = () => {
    setPracticeState(prev => ({
      ...prev,
      isPlaying: !prev.isPlaying
    }))
  }

  const handleTempoChange = (newTempo: number) => {
    setPracticeState(prev => ({
      ...prev,
      currentTempo: Math.max(40, Math.min(200, newTempo))
    }))
  }

  const handleModeChange = (mode: 'listen' | 'practice' | 'assessment') => {
    setPracticeState(prev => ({
      ...prev,
      practiceMode: mode,
      isPlaying: false
    }))
  }

  const handleSequenceChange = (sequence: 'arohanam' | 'avarohanam' | 'both') => {
    setPracticeState(prev => ({
      ...prev,
      currentSequence: sequence,
      swaraIndex: 0,
      isPlaying: false
    }))
  }

  const handleReset = () => {
    setPracticeState(prev => ({
      ...prev,
      isPlaying: false,
      swaraIndex: 0,
      completedCycles: 0,
      accuracy: 0
    }))
    setCurrentSwara('')
    setTargetSwara('')
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

        {/* Pattern Display */}
        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <div className="space-y-2">
            <h4 className="font-semibold text-gray-800">आरोहणम् (Arohanam)</h4>
            <div className="flex flex-wrap gap-2">
              {currentPattern.arohanam.map((swara, index) => (
                <motion.span
                  key={`arohanam-${index}`}
                  className={cn(
                    "px-3 py-1 rounded-full border text-sm font-medium transition-all",
                    practiceState.currentSequence !== 'avarohanam' &&
                    practiceState.swaraIndex === index && practiceState.isPlaying
                      ? "bg-orange-100 border-orange-400 text-orange-800 scale-110"
                      : "bg-gray-50 border-gray-200 text-gray-700"
                  )}
                  animate={
                    practiceState.currentSequence !== 'avarohanam' &&
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

          <div className="space-y-2">
            <h4 className="font-semibold text-gray-800">अवरोहणम् (Avarohanam)</h4>
            <div className="flex flex-wrap gap-2">
              {currentPattern.avarohanam.map((swara, index) => (
                <motion.span
                  key={`avarohanam-${index}`}
                  className={cn(
                    "px-3 py-1 rounded-full border text-sm font-medium transition-all",
                    practiceState.currentSequence === 'avarohanam' &&
                    practiceState.swaraIndex === index && practiceState.isPlaying
                      ? "bg-blue-100 border-blue-400 text-blue-800 scale-110"
                      : "bg-gray-50 border-gray-200 text-gray-700"
                  )}
                  animate={
                    practiceState.currentSequence === 'avarohanam' &&
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
      <div className="flex justify-center">
        <SwaraWheel
          currentSwara={currentSwara}
          targetSwara={targetSwara}
          confidence={0.8}
          centDeviation={Math.random() * 10 - 5}
          className="w-80 h-80"
        />
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg border shadow-sm p-6 space-y-4">
        {/* Mode Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">Practice Mode</label>
          <div className="flex space-x-2">
            {(['listen', 'practice', 'assessment'] as const).map((mode) => (
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

        {/* Sequence Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">Sequence</label>
          <div className="flex space-x-2">
            {(['arohanam', 'avarohanam', 'both'] as const).map((seq) => (
              <Button
                key={seq}
                variant={practiceState.currentSequence === seq ? "carnatic" : "outline"}
                size="sm"
                onClick={() => handleSequenceChange(seq)}
                className="capitalize"
              >
                {seq === 'arohanam' ? 'आरोहणम्' : seq === 'avarohanam' ? 'अवरोहणम्' : 'Both'}
              </Button>
            ))}
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

        {/* Playback Controls */}
        <div className="flex items-center justify-center space-x-4">
          <Button
            variant={practiceState.isPlaying ? "destructive" : "carnatic"}
            size="lg"
            onClick={handlePlayPause}
            className="flex items-center space-x-2"
          >
            {practiceState.isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
            <span>{practiceState.isPlaying ? 'Pause' : 'Play'}</span>
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
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setShowSettings(false)}
          >
            <motion.div
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
    </div>
  )
}

export { SaraliInterface }