import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic, MicOff, Play, Pause, Square, RotateCcw, Download,
  Volume2, VolumeX, Settings, AudioWaveform, Timer, AlertCircle
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'
import AudioVisualizer from './AudioVisualizer'
import { VoiceCalibration } from './VoiceCalibration'

interface RecordingInterfaceProps {
  onRecordingComplete?: (audioBlob: Blob, analysis: AudioAnalysis) => void
  onPitchDetection?: (frequency: number, note: string, confidence: number) => void
  referenceFrequency?: number
  className?: string
}

interface AudioAnalysis {
  duration: number
  averagePitch: number
  pitchStability: number
  volumeConsistency: number
  detectedNotes: Array<{
    note: string
    frequency: number
    timestamp: number
    confidence: number
  }>
}

interface RecordingState {
  isRecording: boolean
  isPlaying: boolean
  isPaused: boolean
  currentTime: number
  duration: number
  volume: number
  isMuted: boolean
}

const RecordingInterface: React.FC<RecordingInterfaceProps> = ({
  onRecordingComplete,
  onPitchDetection,
  referenceFrequency = 261.63, // Middle C
  className
}) => {
  const [recordingState, setRecordingState] = useState<RecordingState>({
    isRecording: false,
    isPlaying: false,
    isPaused: false,
    currentTime: 0,
    duration: 0,
    volume: 0.7,
    isMuted: false
  })

  const [audioData, setAudioData] = useState<Float32Array | null>(null)
  const [frequencyData, setFrequencyData] = useState<Uint8Array | null>(null)
  const [currentPitch, setCurrentPitch] = useState<{
    frequency: number
    note: string
    confidence: number
  } | null>(null)

  const [error, setError] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [showCalibration, setShowCalibration] = useState(false)
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const animationFrameRef = useRef<number>()
  const timerRef = useRef<NodeJS.Timeout>()
  const chunksRef = useRef<Blob[]>([])

  // Note frequency mapping for pitch detection
  const noteFrequencies = {
    'C': [16.35, 32.70, 65.41, 130.81, 261.63, 523.25, 1046.50],
    'C#': [17.32, 34.65, 69.30, 138.59, 277.18, 554.37, 1108.73],
    'D': [18.35, 36.71, 73.42, 146.83, 293.66, 587.33, 1174.66],
    'D#': [19.45, 38.89, 77.78, 155.56, 311.13, 622.25, 1244.51],
    'E': [20.60, 41.20, 82.41, 164.81, 329.63, 659.25, 1318.51],
    'F': [21.83, 43.65, 87.31, 174.61, 349.23, 698.46, 1396.91],
    'F#': [23.12, 46.25, 92.50, 185.00, 369.99, 739.99, 1479.98],
    'G': [24.50, 49.00, 98.00, 196.00, 392.00, 783.99, 1567.98],
    'G#': [25.96, 51.91, 103.83, 207.65, 415.30, 830.61, 1661.22],
    'A': [27.50, 55.00, 110.00, 220.00, 440.00, 880.00, 1760.00],
    'A#': [29.14, 58.27, 116.54, 233.08, 466.16, 932.33, 1864.66],
    'B': [30.87, 61.74, 123.47, 246.94, 493.88, 987.77, 1975.53]
  }

  useEffect(() => {
    initializeAudio()
    return () => {
      cleanup()
    }
  }, [])

  useEffect(() => {
    if (recordingState.isRecording && analyserRef.current) {
      startPitchDetection()
    } else {
      stopPitchDetection()
    }
  }, [recordingState.isRecording])

  const initializeAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: false,
          sampleRate: 44100
        }
      })

      streamRef.current = stream
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()

      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()

      analyserRef.current.fftSize = 2048
      analyserRef.current.smoothingTimeConstant = 0.8

      sourceRef.current.connect(analyserRef.current)

      // Initialize MediaRecorder
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setRecordedBlob(audioBlob)
        chunksRef.current = []

        // Analyze the recording
        analyzeRecording(audioBlob)
      }

    } catch (err: any) {
      setError('Failed to access microphone: ' + err.message)
    }
  }

  const cleanup = () => {
    stopPitchDetection()

    if (timerRef.current) clearInterval(timerRef.current)
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop())
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }
  }

  const startRecording = () => {
    if (!mediaRecorderRef.current || recordingState.isRecording) return

    try {
      setError(null)
      chunksRef.current = []
      mediaRecorderRef.current.start(100) // Collect data every 100ms

      setRecordingState(prev => ({
        ...prev,
        isRecording: true,
        currentTime: 0,
        duration: 0
      }))

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingState(prev => ({
          ...prev,
          currentTime: prev.currentTime + 0.1
        }))
      }, 100)

    } catch (err: any) {
      setError('Failed to start recording: ' + err.message)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }

    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = undefined
    }

    setRecordingState(prev => ({
      ...prev,
      isRecording: false,
      duration: prev.currentTime
    }))
  }

  const startPitchDetection = () => {
    if (!analyserRef.current) return

    const bufferLength = analyserRef.current.frequencyBinCount
    const dataArray = new Float32Array(bufferLength)
    const freqArray = new Uint8Array(bufferLength)

    const detectPitch = () => {
      if (!analyserRef.current) return

      analyserRef.current.getFloatTimeDomainData(dataArray)
      analyserRef.current.getByteFrequencyData(freqArray)

      setAudioData(new Float32Array(dataArray))
      setFrequencyData(new Uint8Array(freqArray))

      // Simple autocorrelation pitch detection
      const pitch = autoCorrelate(dataArray, audioContextRef.current!.sampleRate)

      if (pitch !== -1) {
        const note = frequencyToNote(pitch)
        const confidence = calculateConfidence(dataArray)

        setCurrentPitch({ frequency: pitch, note, confidence })

        if (onPitchDetection) {
          onPitchDetection(pitch, note, confidence)
        }
      }

      if (recordingState.isRecording) {
        animationFrameRef.current = requestAnimationFrame(detectPitch)
      }
    }

    detectPitch()
  }

  const stopPitchDetection = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = undefined
    }
  }

  const autoCorrelate = (buffer: Float32Array, sampleRate: number): number => {
    const SIZE = buffer.length
    const MAX_SAMPLES = Math.floor(SIZE / 2)
    let bestOffset = -1
    let bestCorrelation = 0
    let rms = 0

    for (let i = 0; i < SIZE; i++) {
      const val = buffer[i]
      rms += val * val
    }
    rms = Math.sqrt(rms / SIZE)

    if (rms < 0.01) return -1 // Not enough signal

    let lastCorrelation = 1
    for (let offset = 1; offset < MAX_SAMPLES; offset++) {
      let correlation = 0
      for (let i = 0; i < MAX_SAMPLES; i++) {
        correlation += Math.abs(buffer[i] - buffer[i + offset])
      }
      correlation = 1 - correlation / MAX_SAMPLES

      if (correlation > 0.9 && correlation > lastCorrelation) {
        bestCorrelation = correlation
        bestOffset = offset
      }
      lastCorrelation = correlation
    }

    if (bestCorrelation > 0.9) {
      return sampleRate / bestOffset
    }
    return -1
  }

  const frequencyToNote = (frequency: number): string => {
    const A4 = 440
    const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    const noteIndex = Math.round(12 * Math.log2(frequency / A4)) + 9
    const octave = Math.floor(noteIndex / 12) + 4
    const note = noteNames[noteIndex % 12]

    return `${note}${octave}`
  }

  const calculateConfidence = (buffer: Float32Array): number => {
    let sum = 0
    for (let i = 0; i < buffer.length; i++) {
      sum += Math.abs(buffer[i])
    }
    return Math.min(sum / buffer.length * 10, 1) // Normalize to 0-1
  }

  const analyzeRecording = async (audioBlob: Blob) => {
    // This would typically involve more sophisticated audio analysis
    // For now, we'll create a basic analysis object
    const analysis: AudioAnalysis = {
      duration: recordingState.currentTime,
      averagePitch: currentPitch?.frequency || 0,
      pitchStability: 0.8, // Mock value
      volumeConsistency: 0.75, // Mock value
      detectedNotes: [] // Would be populated with actual note detection
    }

    if (onRecordingComplete) {
      onRecordingComplete(audioBlob, analysis)
    }
  }

  const playRecording = () => {
    if (!recordedBlob) return

    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }

    const audio = new Audio(URL.createObjectURL(recordedBlob))
    audioRef.current = audio

    audio.addEventListener('loadedmetadata', () => {
      setRecordingState(prev => ({
        ...prev,
        duration: audio.duration
      }))
    })

    audio.addEventListener('timeupdate', () => {
      setRecordingState(prev => ({
        ...prev,
        currentTime: audio.currentTime
      }))
    })

    audio.addEventListener('ended', () => {
      setRecordingState(prev => ({
        ...prev,
        isPlaying: false,
        currentTime: 0
      }))
    })

    audio.volume = recordingState.isMuted ? 0 : recordingState.volume
    audio.play()

    setRecordingState(prev => ({
      ...prev,
      isPlaying: true
    }))
  }

  const pausePlayback = () => {
    if (audioRef.current) {
      audioRef.current.pause()
    }
    setRecordingState(prev => ({
      ...prev,
      isPlaying: false
    }))
  }

  const resetRecording = () => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }

    setRecordedBlob(null)
    setCurrentPitch(null)
    setRecordingState(prev => ({
      ...prev,
      isRecording: false,
      isPlaying: false,
      currentTime: 0,
      duration: 0
    }))
  }

  const downloadRecording = () => {
    if (!recordedBlob) return

    const url = URL.createObjectURL(recordedBlob)
    const a = document.createElement('a')
    a.href = url
    a.download = `recording-${new Date().toISOString()}.webm`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Error Display */}
      {error && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700"
        >
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </motion.div>
      )}

      {/* Audio Visualizer */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <AudioVisualizer
          audioData={audioData}
          frequencyData={frequencyData}
          isRecording={recordingState.isRecording}
          currentPitch={currentPitch}
          referenceFrequency={referenceFrequency}
          className="h-40 mb-4"
        />

        {/* Current Pitch Display */}
        {currentPitch && (
          <div className="text-center mb-4">
            <div className="text-2xl font-bold text-orange-600">
              {currentPitch.note}
            </div>
            <div className="text-sm text-gray-600">
              {currentPitch.frequency.toFixed(1)} Hz
              <span className="ml-2">
                Confidence: {(currentPitch.confidence * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Recording Controls */}
      <div className="bg-white rounded-lg border shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Timer className="h-5 w-5 text-gray-500" />
            <span className="text-lg font-mono">
              {formatTime(recordingState.currentTime)}
              {recordingState.duration > 0 && (
                <span className="text-gray-500">
                  {' / ' + formatTime(recordingState.duration)}
                </span>
              )}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowCalibration(true)}
            >
              <Settings className="h-5 w-5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setRecordingState(prev => ({
                ...prev,
                isMuted: !prev.isMuted
              }))}
            >
              {recordingState.isMuted ? (
                <VolumeX className="h-5 w-5" />
              ) : (
                <Volume2 className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>

        {/* Main Controls */}
        <div className="flex items-center justify-center space-x-4">
          {!recordingState.isRecording ? (
            <Button
              size="lg"
              variant="carnatic"
              onClick={startRecording}
              className="flex items-center space-x-2"
            >
              <Mic className="h-6 w-6" />
              <span>Start Recording</span>
            </Button>
          ) : (
            <Button
              size="lg"
              variant="destructive"
              onClick={stopRecording}
              className="flex items-center space-x-2"
            >
              <Square className="h-6 w-6" />
              <span>Stop Recording</span>
            </Button>
          )}

          {recordedBlob && (
            <>
              {!recordingState.isPlaying ? (
                <Button
                  size="lg"
                  variant="outline"
                  onClick={playRecording}
                  className="flex items-center space-x-2"
                >
                  <Play className="h-5 w-5" />
                  <span>Play</span>
                </Button>
              ) : (
                <Button
                  size="lg"
                  variant="outline"
                  onClick={pausePlayback}
                  className="flex items-center space-x-2"
                >
                  <Pause className="h-5 w-5" />
                  <span>Pause</span>
                </Button>
              )}

              <Button
                variant="outline"
                onClick={resetRecording}
              >
                <RotateCcw className="h-5 w-5" />
              </Button>

              <Button
                variant="outline"
                onClick={downloadRecording}
              >
                <Download className="h-5 w-5" />
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Voice Calibration Modal */}
      <VoiceCalibration
        isOpen={showCalibration}
        onClose={() => setShowCalibration(false)}
        onCalibrationComplete={(settings) => {
          console.log('Calibration complete:', settings)
          setShowCalibration(false)
        }}
      />
    </div>
  )
}

export { RecordingInterface }