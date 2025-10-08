// Core audio-related type definitions for the Carnatic Music Learning Platform

export type NoteString = 'C' | 'C#' | 'Db' | 'D' | 'D#' | 'Eb' | 'E' | 'F' | 'F#' | 'Gb' | 'G' | 'G#' | 'Ab' | 'A' | 'A#' | 'Bb' | 'B'

export type SwaraName = 'Sa' | 'Ri' | 'Ga' | 'Ma' | 'Pa' | 'Dha' | 'Ni'

export type OctaveNumber = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8

export interface AudioDeviceInfo extends MediaDeviceInfo {
  sampleRateRange?: [number, number]
  latency?: number
  qualityScore?: number
  isRecommended?: boolean
}

export interface AudioConfig {
  sampleRate: number
  bufferSize: number
  fftSize: number
  smoothingTimeConstant: number
  minDecibels: number
  maxDecibels: number
  channels: number
  bitDepth: 16 | 24 | 32
}

export interface PitchInfo {
  frequency: number
  note: NoteString
  octave: OctaveNumber
  cents: number
  confidence: number
  timestamp: number
  swara?: SwaraName
  ragaAdjustment?: number
}

export interface AudioAnalysis {
  pitch: PitchInfo
  amplitude: number
  spectralCentroid: number
  zeroCrossingRate: number
  mfcc: number[]
  harmonics: {
    frequency: number
    amplitude: number
  }[]
  formants: number[]
  quality: AudioQuality
}

export interface AudioQuality {
  clarity: number // 0-1, signal clarity
  stability: number // 0-1, pitch stability
  intonation: number // 0-1, pitch accuracy
  tone: number // 0-1, tonal quality
  overall: number // 0-1, combined score
}

export interface RecordingMetadata {
  sessionId?: string
  exerciseType: string
  exerciseId?: string
  raga?: string
  tempo?: number
  duration: number
  sampleRate: number
  channels: number
  bitDepth: number
  format: string
  userId: string
  timestamp: number
}

export interface AudioRecording {
  id: string
  metadata: RecordingMetadata
  audioBlob: Blob
  pitchData: PitchInfo[]
  analysis: AudioAnalysis[]
  waveformData?: Float32Array
  spectrumData?: Float32Array
  createdAt: number
  updatedAt: number
}

export interface CalibrationData {
  baseFrequency: number // User's comfortable singing pitch (usually around Middle C)
  pitchRange: [number, number] // [lowest, highest] comfortable frequencies
  stabilityThreshold: number // Minimum stability required for accurate detection
  testResults: {
    targetFrequency: number
    measuredFrequency: number
    accuracy: number
    stability: number
    attempts: number
  }[]
  voiceCharacteristics: {
    timbre: 'bright' | 'warm' | 'neutral' | 'dark'
    vibrato: {
      present: boolean
      rate?: number // Hz
      extent?: number // cents
    }
    breathSupport: number // 0-1
    resonance: number // 0-1
  }
  createdAt: number
  lastUpdated: number
}

export interface AudioProcessingOptions {
  noiseReduction: boolean
  autoGain: boolean
  pitchCorrection: boolean
  realTimeAnalysis: boolean
  harmonicEnhancement: boolean
  formantCorrection: boolean
}

export interface RealTimeFeedback {
  pitchAccuracy: {
    currentNote: NoteString
    targetNote: NoteString
    centsOff: number
    direction: 'higher' | 'lower' | 'correct'
    confidence: number
  }
  rhythmAccuracy: {
    expectedBeat: number
    actualBeat: number
    deviation: number // milliseconds
    isSyncronized: boolean
  }
  intonation: {
    score: number // 0-1
    suggestion: string
    ragaCompliance: number // 0-1
  }
  expression: {
    dynamics: number // 0-1, volume variation
    phrasing: number // 0-1, phrase structure
    emotion: number // 0-1, emotional expression
  }
}

export interface AudioVisualizationData {
  waveform: {
    timeData: Float32Array
    peakLevel: number
    rmsLevel: number
  }
  spectrum: {
    frequencyData: Float32Array
    dominantFrequency: number
    harmonics: number[]
  }
  pitch: {
    frequency: number
    confidence: number
    stability: number
    history: number[] // Last N pitch detections
  }
  volume: {
    level: number
    peak: number
    average: number
  }
}

export interface TuningReference {
  name: string
  description: string
  baseFrequency: number // A4 frequency
  temperament: 'equal' | 'just' | 'pythagorean' | 'meanTone'
  adjustments: {
    [key in NoteString]?: number // Cents deviation from equal temperament
  }
}

export interface AudioEffect {
  id: string
  name: string
  type: 'reverb' | 'delay' | 'chorus' | 'compressor' | 'eq' | 'filter'
  parameters: {
    [key: string]: number | boolean | string
  }
  enabled: boolean
}

export interface AudioMixer {
  channels: {
    id: string
    name: string
    type: 'microphone' | 'playback' | 'metronome' | 'reference'
    volume: number
    pan: number
    muted: boolean
    soloed: boolean
    effects: AudioEffect[]
  }[]
  masterVolume: number
  masterEffects: AudioEffect[]
}

export interface SoundSynthesis {
  waveType: OscillatorType
  attack: number // seconds
  decay: number // seconds
  sustain: number // 0-1
  release: number // seconds
  harmonics?: {
    harmonic: number
    amplitude: number
  }[]
  filters?: {
    type: BiquadFilterType
    frequency: number
    q: number
    gain?: number
  }[]
}

export interface AudioWorkletMessage {
  type: 'pitchData' | 'audioLevel' | 'spectrumData' | 'error'
  data: any
  timestamp: number
}

export interface PerformanceMetrics {
  latency: {
    input: number // milliseconds
    processing: number // milliseconds
    output: number // milliseconds
    total: number // milliseconds
  }
  cpuUsage: number // 0-1
  memoryUsage: number // bytes
  bufferUnderruns: number
  sampleDropouts: number
  qualityScore: number // 0-1
}

// Carnatic Music specific types
export interface RagaDefinition {
  name: string
  nameDevanagari: string
  melakarta?: number
  arohanam: SwaraName[]
  avarohanam: SwaraName[]
  characteristics: string
  swaraAdjustments: {
    [key in SwaraName]?: number // Cents adjustment
  }
  gamakas: {
    swara: SwaraName
    type: 'kampita' | 'andolita' | 'sphurita' | 'ahata' | 'pratyahata'
    intensity: number // 0-1
  }[]
  visesha: string[] // Special notes or phrases
}

export interface TalaDefinition {
  name: string
  nameDevanagari: string
  beats: number
  subdivisions: number[]
  pattern: ('ta' | 'ki' | 'ta-ka' | 'ta-ki-ta' | 'ta-ka-dhi-mi')[]
  tempo: {
    min: number
    max: number
    default: number
  }
}

export interface GamakaPattern {
  name: string
  type: 'kampita' | 'andolita' | 'sphurita' | 'ahata' | 'pratyahata'
  startNote: SwaraName
  endNote: SwaraName
  duration: number // milliseconds
  frequency: number // Hz for kampita/andolita
  intensity: number // 0-1
  shape: 'linear' | 'exponential' | 'logarithmic' | 'sinusoidal'
}

// Export utility types
export type AudioEventType = 'pitchDetected' | 'recordingStarted' | 'recordingStopped' | 'analysisComplete' | 'deviceChanged' | 'error'

export interface AudioEvent {
  type: AudioEventType
  data?: any
  timestamp: number
  source: string
}

export type AudioQualityLevel = 'low' | 'medium' | 'high' | 'lossless'

export interface AudioFormat {
  name: string
  extension: string
  mimeType: string
  compression: 'none' | 'lossless' | 'lossy'
  qualityLevels: AudioQualityLevel[]
  maxChannels: number
  maxSampleRate: number
  maxBitDepth: number
}

// Re-export commonly used browser audio types
export type {
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
}