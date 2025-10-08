import React, { createContext, useContext, useState, useRef, useCallback, ReactNode, useEffect } from 'react'

export interface AudioConfig {
  sampleRate: number
  bufferSize: number
  fftSize: number
  smoothingTimeConstant: number
  minDecibels: number
  maxDecibels: number
}

export interface PitchInfo {
  frequency: number
  note: string
  octave: number
  cents: number
  confidence: number
  timestamp: number
}

export interface AudioState {
  isRecording: boolean
  isPlaying: boolean
  isAnalyzing: boolean
  currentPitch: PitchInfo | null
  audioLevel: number
  error: string | null
  deviceId: string | null
  devices: MediaDeviceInfo[]
}

export interface AudioContextType extends AudioState {
  startRecording: () => Promise<void>
  stopRecording: () => Promise<void>
  startPitchDetection: () => Promise<void>
  stopPitchDetection: () => void
  playFrequency: (frequency: number, duration: number, volume?: number) => Promise<void>
  playNote: (note: string, octave: number, duration: number, volume?: number) => Promise<void>
  generateTone: (frequency: number, duration: number, waveType?: OscillatorType) => Promise<AudioBuffer>
  setDevice: (deviceId: string) => Promise<void>
  refreshDevices: () => Promise<void>
  setConfig: (config: Partial<AudioConfig>) => void
  getAudioLevel: () => number
  clearError: () => void
}

const defaultConfig: AudioConfig = {
  sampleRate: 44100,
  bufferSize: 4096,
  fftSize: 8192,
  smoothingTimeConstant: 0.8,
  minDecibels: -90,
  maxDecibels: -10
}

const AudioContext = createContext<AudioContextType | undefined>(undefined)

export const useAudio = () => {
  const context = useContext(AudioContext)
  if (context === undefined) {
    throw new Error('useAudio must be used within an AudioProvider')
  }
  return context
}

interface AudioProviderProps {
  children: ReactNode
}

export const AudioProvider: React.FC<AudioProviderProps> = ({ children }) => {
  const [state, setState] = useState<AudioState>({
    isRecording: false,
    isPlaying: false,
    isAnalyzing: false,
    currentPitch: null,
    audioLevel: 0,
    error: null,
    deviceId: null,
    devices: []
  })

  const [config, setConfigState] = useState<AudioConfig>(defaultConfig)

  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const microphoneRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const pitchDetectionWorkerRef = useRef<Worker | null>(null)

  useEffect(() => {
    initializeAudioContext()
    refreshDevices()

    return () => {
      cleanup()
    }
  }, [])

  const initializeAudioContext = () => {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
      audioContextRef.current = new AudioContextClass({
        sampleRate: config.sampleRate
      })
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'Failed to initialize audio context'
      }))
    }
  }

  const cleanup = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }

    if (pitchDetectionWorkerRef.current) {
      pitchDetectionWorkerRef.current.terminate()
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop())
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
    }
  }

  const refreshDevices = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices()
      const audioInputs = devices.filter(device => device.kind === 'audioinput')

      setState(prev => ({
        ...prev,
        devices: audioInputs,
        deviceId: audioInputs.length > 0 ? audioInputs[0].deviceId : null
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: 'Failed to enumerate audio devices'
      }))
    }
  }

  const setDevice = async (deviceId: string) => {
    setState(prev => ({ ...prev, deviceId }))

    // Restart recording with new device if currently recording
    if (state.isRecording) {
      await stopRecording()
      await startRecording()
    }
  }

  const startRecording = async () => {
    try {
      if (!audioContextRef.current) {
        initializeAudioContext()
      }

      if (audioContextRef.current?.state === 'suspended') {
        await audioContextRef.current.resume()
      }

      const constraints: MediaStreamConstraints = {
        audio: {
          deviceId: state.deviceId ? { exact: state.deviceId } : undefined,
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
          sampleRate: config.sampleRate
        }
      }

      const stream = await navigator.mediaDevices.getUserMedia(constraints)
      mediaStreamRef.current = stream

      const audioContext = audioContextRef.current!
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = config.fftSize
      analyser.smoothingTimeConstant = config.smoothingTimeConstant
      analyser.minDecibels = config.minDecibels
      analyser.maxDecibels = config.maxDecibels

      const microphone = audioContext.createMediaStreamSource(stream)
      microphone.connect(analyser)

      analyserRef.current = analyser
      microphoneRef.current = microphone

      setState(prev => ({
        ...prev,
        isRecording: true,
        error: null
      }))
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to start recording'
      }))
      throw error
    }
  }

  const stopRecording = async () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop())
      mediaStreamRef.current = null
    }

    if (microphoneRef.current) {
      microphoneRef.current.disconnect()
      microphoneRef.current = null
    }

    analyserRef.current = null

    setState(prev => ({
      ...prev,
      isRecording: false,
      isAnalyzing: false,
      currentPitch: null,
      audioLevel: 0
    }))
  }

  const autoCorrelate = (buffer: Float32Array, sampleRate: number): number => {
    const SIZE = buffer.length
    const MAX_SAMPLES = Math.floor(SIZE / 2)
    let bestOffset = -1
    let bestCorrelation = 0
    let rms = 0

    // Calculate RMS
    for (let i = 0; i < SIZE; i++) {
      const val = buffer[i]
      rms += val * val
    }
    rms = Math.sqrt(rms / SIZE)

    // Not enough signal
    if (rms < 0.01) return -1

    let lastCorrelation = 1
    for (let offset = 1; offset < MAX_SAMPLES; offset++) {
      let correlation = 0
      for (let i = 0; i < MAX_SAMPLES; i++) {
        correlation += Math.abs((buffer[i]) - (buffer[i + offset]))
      }
      correlation = 1 - (correlation / MAX_SAMPLES)

      if (correlation > 0.9 && correlation > lastCorrelation) {
        bestCorrelation = correlation
        bestOffset = offset
      }
      lastCorrelation = correlation
    }

    if (bestOffset === -1 || bestCorrelation < 0.01) return -1

    // Refine using parabolic interpolation
    const y1 = bestOffset > 0 ? bestCorrelation : 0
    const y2 = bestCorrelation
    const y3 = bestOffset < MAX_SAMPLES - 1 ? bestCorrelation : 0

    const a = (y1 - 2 * y2 + y3) / 2
    const b = (y3 - y1) / 2

    if (a) {
      bestOffset = bestOffset - b / (2 * a)
    }

    return sampleRate / bestOffset
  }

  const noteFromFreq = (frequency: number): { note: string; octave: number; cents: number } => {
    const A4 = 440
    const C0 = A4 * Math.pow(2, -4.75)

    if (frequency > 0) {
      const halfSteps = Math.round(12 * Math.log2(frequency / C0))
      const octave = Math.floor(halfSteps / 12)
      const note = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][halfSteps % 12]

      const expectedFreq = C0 * Math.pow(2, halfSteps / 12)
      const cents = Math.floor(1200 * Math.log2(frequency / expectedFreq))

      return { note, octave, cents }
    }

    return { note: '', octave: 0, cents: 0 }
  }

  const analyzePitch = useCallback(() => {
    if (!analyserRef.current || !state.isRecording) return

    const bufferLength = analyserRef.current.frequencyBinCount
    const dataArray = new Float32Array(bufferLength)
    analyserRef.current.getFloatTimeDomainData(dataArray)

    // Calculate audio level
    let sum = 0
    for (let i = 0; i < bufferLength; i++) {
      sum += dataArray[i] * dataArray[i]
    }
    const rms = Math.sqrt(sum / bufferLength)
    const audioLevel = Math.min(Math.max(rms * 100, 0), 100)

    // Detect pitch
    const frequency = autoCorrelate(dataArray, config.sampleRate)

    if (frequency > 0) {
      const { note, octave, cents } = noteFromFreq(frequency)
      const confidence = Math.min(rms * 10, 1)

      setState(prev => ({
        ...prev,
        currentPitch: {
          frequency,
          note,
          octave,
          cents,
          confidence,
          timestamp: Date.now()
        },
        audioLevel
      }))
    } else {
      setState(prev => ({
        ...prev,
        audioLevel,
        currentPitch: null
      }))
    }

    animationFrameRef.current = requestAnimationFrame(analyzePitch)
  }, [state.isRecording, config.sampleRate])

  const startPitchDetection = async () => {
    if (!state.isRecording) {
      await startRecording()
    }

    setState(prev => ({ ...prev, isAnalyzing: true }))
    analyzePitch()
  }

  const stopPitchDetection = () => {
    setState(prev => ({ ...prev, isAnalyzing: false }))

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
  }

  const playFrequency = async (frequency: number, duration: number, volume: number = 0.5) => {
    if (!audioContextRef.current) return

    setState(prev => ({ ...prev, isPlaying: true }))

    try {
      const audioContext = audioContextRef.current
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()

      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)

      oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime)
      oscillator.type = 'sine'

      gainNode.gain.setValueAtTime(0, audioContext.currentTime)
      gainNode.gain.linearRampToValueAtTime(volume, audioContext.currentTime + 0.01)
      gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + duration)

      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + duration)

      return new Promise<void>((resolve) => {
        oscillator.onended = () => {
          setState(prev => ({ ...prev, isPlaying: false }))
          resolve()
        }
      })
    } catch (error) {
      setState(prev => ({
        ...prev,
        isPlaying: false,
        error: 'Failed to play frequency'
      }))
      throw error
    }
  }

  const playNote = async (note: string, octave: number, duration: number, volume: number = 0.5) => {
    const noteMap: { [key: string]: number } = {
      'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
      'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
    }

    const noteNumber = noteMap[note]
    if (noteNumber === undefined) {
      throw new Error(`Invalid note: ${note}`)
    }

    const A4 = 440
    const frequency = A4 * Math.pow(2, (octave * 12 + noteNumber - 57) / 12)

    return playFrequency(frequency, duration, volume)
  }

  const generateTone = async (frequency: number, duration: number, waveType: OscillatorType = 'sine'): Promise<AudioBuffer> => {
    if (!audioContextRef.current) {
      throw new Error('Audio context not initialized')
    }

    const audioContext = audioContextRef.current
    const sampleFrames = Math.ceil(audioContext.sampleRate * duration)
    const audioBuffer = audioContext.createBuffer(1, sampleFrames, audioContext.sampleRate)
    const channelData = audioBuffer.getChannelData(0)

    for (let i = 0; i < sampleFrames; i++) {
      const t = i / audioContext.sampleRate
      let sample = 0

      switch (waveType) {
        case 'sine':
          sample = Math.sin(2 * Math.PI * frequency * t)
          break
        case 'square':
          sample = Math.sign(Math.sin(2 * Math.PI * frequency * t))
          break
        case 'sawtooth':
          sample = 2 * (t * frequency - Math.floor(0.5 + t * frequency))
          break
        case 'triangle':
          sample = 2 * Math.abs(2 * (t * frequency - Math.floor(0.5 + t * frequency))) - 1
          break
      }

      // Apply envelope
      const fadeTime = 0.01
      let envelope = 1
      if (t < fadeTime) {
        envelope = t / fadeTime
      } else if (t > duration - fadeTime) {
        envelope = (duration - t) / fadeTime
      }

      channelData[i] = sample * envelope
    }

    return audioBuffer
  }

  const getAudioLevel = () => state.audioLevel

  const setConfig = (newConfig: Partial<AudioConfig>) => {
    setConfigState(prev => ({ ...prev, ...newConfig }))
  }

  const clearError = () => {
    setState(prev => ({ ...prev, error: null }))
  }

  const value: AudioContextType = {
    ...state,
    startRecording,
    stopRecording,
    startPitchDetection,
    stopPitchDetection,
    playFrequency,
    playNote,
    generateTone,
    setDevice,
    refreshDevices,
    setConfig,
    getAudioLevel,
    clearError
  }

  return (
    <AudioContext.Provider value={value}>
      {children}
    </AudioContext.Provider>
  )
}