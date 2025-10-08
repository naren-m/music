import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'
import {
  Play, Pause, RotateCcw, Volume2, VolumeX, Settings,
  Crown, Star, BookOpen, Music, Target, ChevronDown, ChevronUp
} from 'lucide-react'
import { RecordingInterface } from '@/components/audio/RecordingInterface'
import RagaSelector from '@/components/carnatic/RagaSelector'

interface AlankaramPattern {
  id: number
  name: string
  nameDevanagari: string
  number: number // Traditional alankaram number (1-35)
  category: 'basic' | 'intermediate' | 'advanced' | 'ornate'
  pattern: string[]
  ragaSpecific: boolean
  supportedRagas: string[]
  tempo_range: [number, number]
  description: string
  culturalSignificance: string
  ornamentationTypes: string[]
  practiceNotes: string[]
  completionRequirements: {
    min_accuracy: number
    ornamentation_quality: number
    min_sessions: number
    tempo_milestones: number[]
    raga_variations: number
  }
}

interface AlankaramInterfaceProps {
  currentPattern?: AlankaramPattern
  onPatternSelect: (pattern: AlankaramPattern) => void
  onProgressUpdate: (progress: any) => void
  className?: string
}

interface PracticeState {
  isPlaying: boolean
  currentTempo: number
  currentNoteIndex: number
  selectedRaga: string
  practiceMode: 'listen' | 'practice' | 'ornamentation' | 'cultural'
  accuracy: number
  ornamentationQuality: number
  completedCycles: number
  sessionTime: number
  currentVariation: number
}

const AlankaramInterface: React.FC<AlankaramInterfaceProps> = ({
  currentPattern,
  onPatternSelect,
  onProgressUpdate,
  className
}) => {
  const [practiceState, setPracticeState] = useState<PracticeState>({
    isPlaying: false,
    currentTempo: 80,
    currentNoteIndex: 0,
    selectedRaga: 'Sankarabharanam',
    practiceMode: 'listen',
    accuracy: 0,
    ornamentationQuality: 0,
    completedCycles: 0,
    sessionTime: 0,
    currentVariation: 1
  })

  const [patterns, setPatterns] = useState<AlankaramPattern[]>([])
  const [showRecording, setShowRecording] = useState(false)
  const [showRagaSelector, setShowRagaSelector] = useState(false)
  const [showCulturalInfo, setShowCulturalInfo] = useState(false)
  const [volume, setVolume] = useState(0.7)
  const [isMuted, setIsMuted] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  const intervalRef = useRef<NodeJS.Timeout>()
  const audioContextRef = useRef<AudioContext>()
  const sessionStartRef = useRef<number>(Date.now())

  useEffect(() => {
    loadAlankaramPatterns()
    initializeAudio()
    return () => cleanup()
  }, [])

  useEffect(() => {
    if (practiceState.isPlaying && currentPattern) {
      startPracticeSequence()
    } else {
      stopPracticeSequence()
    }
  }, [practiceState.isPlaying, practiceState.currentTempo, practiceState.selectedRaga, currentPattern])

  const loadAlankaramPatterns = async () => {
    try {
      const response = await fetch('/api/exercises/alankaram/patterns')
      const data = await response.json()
      setPatterns(data)

      if (!currentPattern && data.length > 0) {
        onPatternSelect(data[0])
      }
    } catch (error) {
      console.error('Failed to load Alankaram patterns:', error)
      // Load demo patterns
      setPatterns(generateDemoPatterns())
    }
  }

  const generateDemoPatterns = (): AlankaramPattern[] => {
    return [
      {
        id: 1,
        name: "First Alankaram",
        nameDevanagari: "प्रथम अलंकारम्",
        number: 1,
        category: 'basic',
        pattern: ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
        ragaSpecific: false,
        supportedRagas: ['Sankarabharanam', 'Bilahari', 'Mohana'],
        tempo_range: [60, 120],
        description: "Foundation alankaram focusing on ascending and descending movement",
        culturalSignificance: "This is the fundamental pattern that introduces students to the concept of melodic ornamentation in Carnatic music. It establishes the basic ascending-descending movement that forms the backbone of more complex alankarams.",
        ornamentationTypes: ['Basic gamaka', 'Smooth transitions', 'Note sustention'],
        practiceNotes: [
          "Focus on smooth voice leading between notes",
          "Maintain consistent tempo throughout",
          "Practice with different emphasis on ascending vs descending",
          "Work on breath control for longer phrases"
        ],
        completionRequirements: {
          min_accuracy: 0.85,
          ornamentation_quality: 0.7,
          min_sessions: 8,
          tempo_milestones: [60, 90, 120],
          raga_variations: 2
        }
      },
      {
        id: 2,
        name: "Second Alankaram",
        nameDevanagari: "द्वितीय अलंकारम्",
        number: 2,
        category: 'basic',
        pattern: ['Sa', 'Ri', 'Ga', 'Ri', 'Ga', 'Ma', 'Ga', 'Ma', 'Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
        ragaSpecific: false,
        supportedRagas: ['Sankarabharanam', 'Kalyani', 'Bhairavi'],
        tempo_range: [50, 110],
        description: "Step-wise movement with return patterns",
        culturalSignificance: "Introduces the concept of oscillating movements and prepares the student for more complex ornamentation patterns. This alankaram teaches the importance of return movements in Carnatic music.",
        ornamentationTypes: ['Oscillating gamaka', 'Return patterns', 'Step-wise movement'],
        practiceNotes: [
          "Emphasize the return movements between notes",
          "Practice clean step-wise transitions",
          "Focus on maintaining melodic flow in oscillations",
          "Work on precision in direction changes"
        ],
        completionRequirements: {
          min_accuracy: 0.8,
          ornamentation_quality: 0.75,
          min_sessions: 10,
          tempo_milestones: [50, 80, 110],
          raga_variations: 2
        }
      },
      {
        id: 3,
        name: "Third Alankaram",
        nameDevanagari: "तृतीय अलंकारम्",
        number: 3,
        category: 'intermediate',
        pattern: ['Sa', 'Ga', 'Ri', 'Ma', 'Ga', 'Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
        ragaSpecific: true,
        supportedRagas: ['Sankarabharanam', 'Kalyani', 'Todi', 'Bhairavi'],
        tempo_range: [70, 140],
        description: "Skipping note patterns with raga-specific variations",
        culturalSignificance: "This alankaram introduces skip patterns and raga-specific note treatments. It's crucial for developing an understanding of raga characteristics and how they affect melodic movement.",
        ornamentationTypes: ['Skip patterns', 'Raga-specific gamakas', 'Interval jumps'],
        practiceNotes: [
          "Study raga characteristics before practicing",
          "Focus on clean interval jumps",
          "Practice raga-specific note treatments",
          "Work on maintaining raga bhava throughout"
        ],
        completionRequirements: {
          min_accuracy: 0.85,
          ornamentation_quality: 0.8,
          min_sessions: 12,
          tempo_milestones: [70, 100, 140],
          raga_variations: 3
        }
      },
      {
        id: 15,
        name: "Fifteenth Alankaram",
        nameDevanagari: "पञ्चदश अलंकारम्",
        number: 15,
        category: 'advanced',
        pattern: ['Sa', 'Ri', 'Ga', 'Ma', 'Pa', 'Da', 'Ni', 'Sa', 'Ni', 'Da', 'Pa', 'Ma', 'Ga', 'Ri', 'Sa'],
        ragaSpecific: true,
        supportedRagas: ['Sankarabharanam', 'Kalyani', 'Harikambhoji', 'Dhanyasi'],
        tempo_range: [80, 160],
        description: "Full octave coverage with complex ornamentations",
        culturalSignificance: "This advanced alankaram covers the full octave and is essential for developing complete melodic control. It incorporates all the techniques learned in previous alankarams.",
        ornamentationTypes: ['Full octave gamakas', 'Complex ornamentations', 'Advanced note combinations'],
        practiceNotes: [
          "Master all previous alankarams before attempting",
          "Focus on octave-spanning breath control",
          "Practice advanced gamaka combinations",
          "Work on seamless octave transitions"
        ],
        completionRequirements: {
          min_accuracy: 0.9,
          ornamentation_quality: 0.9,
          min_sessions: 20,
          tempo_milestones: [80, 120, 160],
          raga_variations: 4
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
      const note = currentPattern.pattern[noteIndex]

      if (!isMuted) {
        playNote(note, practiceState.selectedRaga)
      }

      setPracticeState(prev => ({
        ...prev,
        currentNoteIndex: noteIndex,
        sessionTime: (Date.now() - sessionStartRef.current) / 1000
      }))

      noteIndex = (noteIndex + 1) % currentPattern.pattern.length

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

  const playNote = (note: string, raga: string) => {
    if (!audioContextRef.current) return

    // Base frequencies for Sankarabharanam (Major scale)
    const baseFrequencies = {
      'Sa': 261.63, 'Ri': 293.66, 'Ga': 329.63, 'Ma': 349.23,
      'Pa': 392.00, 'Da': 440.00, 'Ni': 493.88
    }

    // Apply raga-specific microtonal adjustments
    const ragaAdjustments = getRagaAdjustments(raga)
    const frequency = baseFrequencies[note as keyof typeof baseFrequencies] || 261.63
    const adjustedFreq = frequency * (ragaAdjustments[note] || 1.0)

    const duration = (60 / practiceState.currentTempo) * 0.8

    const oscillator = audioContextRef.current.createOscillator()
    const gainNode = audioContextRef.current.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContextRef.current.destination)

    oscillator.frequency.setValueAtTime(adjustedFreq, audioContextRef.current.currentTime)
    oscillator.type = 'sine'

    // Add subtle ornamentation for advanced patterns
    if (currentPattern && currentPattern.category !== 'basic') {
      // Add slight pitch bend for gamakas
      const bendAmount = 1.02 // 2% pitch bend
      oscillator.frequency.exponentialRampToValueAtTime(
        adjustedFreq * bendAmount,
        audioContextRef.current.currentTime + duration * 0.3
      )
      oscillator.frequency.exponentialRampToValueAtTime(
        adjustedFreq,
        audioContextRef.current.currentTime + duration * 0.7
      )
    }

    gainNode.gain.setValueAtTime(0, audioContextRef.current.currentTime)
    gainNode.gain.linearRampToValueAtTime(volume * 0.3, audioContextRef.current.currentTime + 0.01)
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContextRef.current.currentTime + duration)

    oscillator.start(audioContextRef.current.currentTime)
    oscillator.stop(audioContextRef.current.currentTime + duration)
  }

  const getRagaAdjustments = (raga: string): Record<string, number> => {
    const adjustments: Record<string, Record<string, number>> = {
      'Sankarabharanam': { 'Sa': 1.0, 'Ri': 1.0, 'Ga': 1.0, 'Ma': 1.0, 'Pa': 1.0, 'Da': 1.0, 'Ni': 1.0 },
      'Kalyani': { 'Sa': 1.0, 'Ri': 1.0, 'Ga': 1.0, 'Ma': 1.045, 'Pa': 1.0, 'Da': 1.0, 'Ni': 1.0 }, // Prati madhyama
      'Todi': { 'Sa': 1.0, 'Ri': 0.95, 'Ga': 0.94, 'Ma': 1.045, 'Pa': 1.0, 'Da': 0.95, 'Ni': 0.94 },
      'Bhairavi': { 'Sa': 1.0, 'Ri': 0.95, 'Ga': 0.94, 'Ma': 1.0, 'Pa': 1.0, 'Da': 0.95, 'Ni': 0.94 }
    }
    return adjustments[raga] || adjustments['Sankarabharanam']
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

  const handleModeChange = (mode: PracticeState['practiceMode']) => {
    setPracticeState(prev => ({
      ...prev,
      practiceMode: mode,
      isPlaying: false
    }))
  }

  const handleRagaChange = (raga: string) => {
    setPracticeState(prev => ({
      ...prev,
      selectedRaga: raga,
      isPlaying: false
    }))
  }

  const handleReset = () => {
    setPracticeState(prev => ({
      ...prev,
      isPlaying: false,
      currentNoteIndex: 0,
      completedCycles: 0,
      accuracy: 0,
      ornamentationQuality: 0,
      sessionTime: 0
    }))
    sessionStartRef.current = Date.now()
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'basic': return 'text-green-600 bg-green-100'
      case 'intermediate': return 'text-yellow-600 bg-yellow-100'
      case 'advanced': return 'text-orange-600 bg-orange-100'
      case 'ornate': return 'text-purple-600 bg-purple-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const getFilteredPatterns = () => {
    if (selectedCategory === 'all') return patterns
    return patterns.filter(pattern => pattern.category === selectedCategory)
  }

  if (!currentPattern) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto"></div>
          <p className="text-gray-600">Loading Alankaram patterns...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">अलंकारम्</h1>
        <h2 className="text-xl text-gray-700">Alankaram</h2>
        <p className="text-gray-600">Traditional Ornamental Exercise Patterns</p>
      </div>

      {/* Pattern Info */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-lg border shadow-sm p-6"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center space-x-3">
              <Crown className="h-6 w-6 text-purple-600" />
              <div>
                <h3 className="text-xl font-bold text-gray-900">{currentPattern.name}</h3>
                <p className="text-lg text-purple-600 font-medium">{currentPattern.nameDevanagari}</p>
              </div>
            </div>
            <div className="flex items-center space-x-3 mt-2">
              <span className={cn(
                "inline-block px-2 py-1 rounded-full text-xs font-medium",
                getCategoryColor(currentPattern.category)
              )}>
                #{currentPattern.number} - {currentPattern.category}
              </span>
              {currentPattern.ragaSpecific && (
                <span className="inline-block px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-600">
                  Raga Specific
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowCulturalInfo(!showCulturalInfo)}
            >
              <BookOpen className="h-4 w-4 mr-1" />
              Cultural Info
            </Button>
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

        {/* Cultural Information */}
        <AnimatePresence>
          {showCulturalInfo && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6 p-4 bg-purple-50 border border-purple-200 rounded-lg"
            >
              <h4 className="font-semibold text-purple-800 mb-2 flex items-center">
                <Star className="h-4 w-4 mr-2" />
                Cultural Significance
              </h4>
              <p className="text-purple-700 text-sm mb-3">{currentPattern.culturalSignificance}</p>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h5 className="font-medium text-purple-800 mb-1">Ornamentation Types:</h5>
                  <ul className="text-sm text-purple-700 list-disc list-inside">
                    {currentPattern.ornamentationTypes.map((type, index) => (
                      <li key={index}>{type}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h5 className="font-medium text-purple-800 mb-1">Practice Notes:</h5>
                  <ul className="text-sm text-purple-700 list-disc list-inside">
                    {currentPattern.practiceNotes.map((note, index) => (
                      <li key={index}>{note}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Pattern Display */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-semibold text-gray-800">Pattern Structure</h4>
            <div className="text-sm text-gray-600">
              Raga: <span className="font-medium text-purple-600">{practiceState.selectedRaga}</span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowRagaSelector(true)}
                className="ml-2"
              >
                Change
              </Button>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {currentPattern.pattern.map((note, index) => (
              <motion.div
                key={index}
                className={cn(
                  "px-3 py-2 rounded-lg border text-sm font-medium transition-all",
                  practiceState.currentNoteIndex === index && practiceState.isPlaying
                    ? "border-purple-400 bg-purple-100 text-purple-800 scale-110 shadow-md"
                    : "border-gray-200 bg-gray-50 text-gray-700"
                )}
                animate={
                  practiceState.currentNoteIndex === index && practiceState.isPlaying
                    ? {
                        scale: [1, 1.1, 1],
                        backgroundColor: ['#f3f4f6', '#e9d5ff', '#f3f4f6'],
                        transition: { duration: 0.6 }
                      }
                    : {}
                }
              >
                {note}
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Raga Selector Modal */}
      {showRagaSelector && (
        <RagaSelector
          selectedRaga={practiceState.selectedRaga}
          availableRagas={currentPattern.supportedRagas}
          onRagaChange={handleRagaChange}
          onClose={() => setShowRagaSelector(false)}
        />
      )}

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
                console.log('Alankaram recording complete:', analysis)
              }}
              onPitchDetection={(freq, note, confidence) => {
                // Update ornamentation quality based on pitch detection
              }}
              className="mb-6"
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Practice Controls */}
      <div className="bg-white rounded-lg border shadow-sm p-6 space-y-6">
        {/* Mode Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">Practice Mode</label>
          <div className="flex flex-wrap gap-2">
            {(['listen', 'practice', 'ornamentation', 'cultural'] as const).map((mode) => (
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
            <span>{practiceState.isPlaying ? 'Pause' : 'Play Alankaram'}</span>
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
            <div className="text-2xl font-bold text-purple-600">{practiceState.completedCycles}</div>
            <div className="text-xs text-gray-600">Cycles</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{practiceState.accuracy.toFixed(1)}%</div>
            <div className="text-xs text-gray-600">Accuracy</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{practiceState.ornamentationQuality.toFixed(1)}%</div>
            <div className="text-xs text-gray-600">Ornamentation</div>
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

      {/* Pattern Library */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-semibold text-gray-800">Traditional Alankaram Library</h4>
          <div className="flex space-x-2">
            {['all', 'basic', 'intermediate', 'advanced', 'ornate'].map((category) => (
              <Button
                key={category}
                variant={selectedCategory === category ? "carnatic" : "outline"}
                size="sm"
                onClick={() => setSelectedCategory(category)}
                className="capitalize"
              >
                {category}
              </Button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {getFilteredPatterns().map((pattern) => (
            <motion.div
              key={pattern.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={cn(
                "p-4 rounded-lg border cursor-pointer transition-all",
                currentPattern.id === pattern.id
                  ? "border-purple-400 bg-purple-50"
                  : "border-gray-200 hover:border-purple-200 hover:bg-purple-25"
              )}
              onClick={() => onPatternSelect(pattern)}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h5 className="font-medium text-gray-900">{pattern.name}</h5>
                  <span className={cn(
                    "px-2 py-1 rounded-full text-xs font-medium",
                    getCategoryColor(pattern.category)
                  )}>
                    #{pattern.number}
                  </span>
                </div>
                <p className="text-sm text-purple-600">{pattern.nameDevanagari}</p>
                <p className="text-sm text-gray-600 line-clamp-2">{pattern.description}</p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                  <span>Tempo: {pattern.tempo_range[0]}-{pattern.tempo_range[1]} BPM</span>
                  <span>{pattern.pattern.length} notes</span>
                </div>
                {pattern.ragaSpecific && (
                  <div className="text-xs text-blue-600">
                    Supports: {pattern.supportedRagas.slice(0, 2).join(', ')}
                    {pattern.supportedRagas.length > 2 && ` +${pattern.supportedRagas.length - 2}`}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}

export { AlankaramInterface }