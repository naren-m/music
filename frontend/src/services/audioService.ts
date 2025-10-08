import { PitchInfo } from '../contexts/AudioContext'

export interface AudioAnalysisResult {
  frequency: number
  note: string
  octave: number
  cents: number
  confidence: number
  pitch_stability: number
  volume: number
}

export interface RecordingData {
  id: string
  user_id: string
  session_id?: string
  duration: number
  sample_rate: number
  audio_data: ArrayBuffer
  analysis: AudioAnalysisResult[]
  created_at: string
}

export interface VoiceCalibrationData {
  user_id: string
  base_frequency: number
  pitch_range: [number, number]
  stability_threshold: number
  calibration_data: {
    test_frequencies: number[]
    measured_frequencies: number[]
    accuracy_scores: number[]
  }
  created_at: string
}

class AudioService {
  private baseUrl = '/api/audio'

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('auth_token')
    const url = `${this.baseUrl}${endpoint}`

    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
    }

    const response = await fetch(url, config)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  /**
   * Submit audio data for pitch analysis
   */
  async analyzeAudio(audioBlob: Blob, metadata?: {
    exercise_type?: string
    raga?: string
    tempo?: number
    session_id?: string
  }): Promise<AudioAnalysisResult> {
    const formData = new FormData()
    formData.append('audio', audioBlob)

    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata))
    }

    const token = localStorage.getItem('auth_token')
    const response = await fetch(`${this.baseUrl}/analyze`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: formData,
    })

    if (!response.ok) {
      throw new Error('Audio analysis failed')
    }

    return response.json()
  }

  /**
   * Save a recording to the server
   */
  async saveRecording(audioBlob: Blob, metadata: {
    session_id?: string
    exercise_type: string
    duration: number
    sample_rate: number
    pitch_data?: PitchInfo[]
  }): Promise<RecordingData> {
    const formData = new FormData()
    formData.append('audio', audioBlob)
    formData.append('metadata', JSON.stringify(metadata))

    const token = localStorage.getItem('auth_token')
    const response = await fetch(`${this.baseUrl}/recordings`, {
      method: 'POST',
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
      body: formData,
    })

    if (!response.ok) {
      throw new Error('Failed to save recording')
    }

    return response.json()
  }

  /**
   * Get user's recordings
   */
  async getRecordings(filters?: {
    session_id?: string
    exercise_type?: string
    date_range?: [string, string]
    limit?: number
    offset?: number
  }): Promise<RecordingData[]> {
    const params = new URLSearchParams()
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          if (Array.isArray(value)) {
            params.append(`${key}[]`, value.join(','))
          } else {
            params.append(key, value.toString())
          }
        }
      })
    }

    const queryString = params.toString()
    const url = queryString ? `/recordings?${queryString}` : '/recordings'

    return this.request<RecordingData[]>(url)
  }

  /**
   * Get a specific recording
   */
  async getRecording(recordingId: string): Promise<RecordingData> {
    return this.request<RecordingData>(`/recordings/${recordingId}`)
  }

  /**
   * Delete a recording
   */
  async deleteRecording(recordingId: string): Promise<void> {
    await this.request(`/recordings/${recordingId}`, {
      method: 'DELETE',
    })
  }

  /**
   * Get audio file as blob for playback
   */
  async getAudioBlob(recordingId: string): Promise<Blob> {
    const token = localStorage.getItem('auth_token')
    const response = await fetch(`${this.baseUrl}/recordings/${recordingId}/audio`, {
      headers: {
        ...(token && { 'Authorization': `Bearer ${token}` }),
      },
    })

    if (!response.ok) {
      throw new Error('Failed to fetch audio data')
    }

    return response.blob()
  }

  /**
   * Submit voice calibration data
   */
  async saveVoiceCalibration(calibrationData: Omit<VoiceCalibrationData, 'user_id' | 'created_at'>): Promise<VoiceCalibrationData> {
    return this.request<VoiceCalibrationData>('/calibration', {
      method: 'POST',
      body: JSON.stringify(calibrationData),
    })
  }

  /**
   * Get user's voice calibration data
   */
  async getVoiceCalibration(): Promise<VoiceCalibrationData | null> {
    try {
      return await this.request<VoiceCalibrationData>('/calibration')
    } catch (error) {
      if (error instanceof Error && error.message.includes('404')) {
        return null
      }
      throw error
    }
  }

  /**
   * Generate reference tones for exercises
   */
  async generateReferenceTones(config: {
    raga: string
    base_frequency: number
    swaras: string[]
    duration?: number
    format?: 'wav' | 'mp3'
  }): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/generate-tones`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(localStorage.getItem('auth_token') && {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }),
      },
      body: JSON.stringify(config),
    })

    if (!response.ok) {
      throw new Error('Failed to generate reference tones')
    }

    return response.blob()
  }

  /**
   * Get real-time pitch correction suggestions
   */
  async getPitchCorrection(currentPitch: PitchInfo, targetNote: string, raga: string): Promise<{
    suggestion: 'higher' | 'lower' | 'correct'
    cents_off: number
    confidence: number
    raga_specific_adjustments?: {
      note: string
      adjustment_cents: number
      cultural_context: string
    }
  }> {
    return this.request('/pitch-correction', {
      method: 'POST',
      body: JSON.stringify({
        current_pitch: currentPitch,
        target_note: targetNote,
        raga: raga,
      }),
    })
  }

  /**
   * Batch process multiple recordings for analysis
   */
  async batchAnalyzeRecordings(recordingIds: string[]): Promise<{
    recording_id: string
    analysis: AudioAnalysisResult
    status: 'completed' | 'failed' | 'processing'
    error?: string
  }[]> {
    return this.request('/batch-analyze', {
      method: 'POST',
      body: JSON.stringify({ recording_ids: recordingIds }),
    })
  }

  /**
   * Get audio processing settings for user
   */
  async getAudioSettings(): Promise<{
    noise_reduction: boolean
    auto_gain: boolean
    pitch_correction: boolean
    real_time_analysis: boolean
    buffer_size: number
    sample_rate: number
  }> {
    return this.request('/settings')
  }

  /**
   * Update audio processing settings
   */
  async updateAudioSettings(settings: Partial<{
    noise_reduction: boolean
    auto_gain: boolean
    pitch_correction: boolean
    real_time_analysis: boolean
    buffer_size: number
    sample_rate: number
  }>): Promise<void> {
    await this.request('/settings', {
      method: 'PATCH',
      body: JSON.stringify(settings),
    })
  }

  /**
   * Get supported audio formats and quality settings
   */
  async getSupportedFormats(): Promise<{
    input_formats: string[]
    output_formats: string[]
    sample_rates: number[]
    bit_depths: number[]
    quality_presets: {
      name: string
      description: string
      settings: any
    }[]
  }> {
    return this.request('/formats')
  }

  /**
   * Test audio device capabilities
   */
  async testAudioDevice(deviceId: string): Promise<{
    device_id: string
    is_supported: boolean
    sample_rate_range: [number, number]
    latency: number
    quality_score: number
    recommendations: string[]
  }> {
    return this.request('/test-device', {
      method: 'POST',
      body: JSON.stringify({ device_id: deviceId }),
    })
  }
}

// Export singleton instance
export const audioService = new AudioService()

// Export utility functions
export const convertBlobToArrayBuffer = (blob: Blob): Promise<ArrayBuffer> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as ArrayBuffer)
    reader.onerror = reject
    reader.readAsArrayBuffer(blob)
  })
}

export const convertArrayBufferToBlob = (buffer: ArrayBuffer, mimeType: string = 'audio/wav'): Blob => {
  return new Blob([buffer], { type: mimeType })
}

export const formatDuration = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export const frequencyToNote = (frequency: number): { note: string; octave: number; cents: number } => {
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

export default audioService