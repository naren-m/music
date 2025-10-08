import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Mic, Volume2, Settings, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'

interface VoiceCalibrationProps {
  isOpen: boolean
  onClose: () => void
  onCalibrationComplete: (settings: CalibrationSettings) => void
}

interface CalibrationSettings {
  microphoneSensitivity: number
  backgroundNoiseLevel: number
  userVoiceRange: {
    minFrequency: number
    maxFrequency: number
  }
  optimalVolume: number
  pitchDetectionThreshold: number
}

interface CalibrationStep {
  id: string
  title: string
  description: string
  instruction: string
  completed: boolean
  data?: any
}

const VoiceCalibration: React.FC<VoiceCalibrationProps> = ({
  isOpen,
  onClose,
  onCalibrationComplete
}) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [isRecording, setIsRecording] = useState(false)
  const [calibrationData, setCalibrationData] = useState<Partial<CalibrationSettings>>({})
  const [error, setError] = useState<string | null>(null)

  const mediaStreamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const animationFrameRef = useRef<number>()

  const [steps, setSteps] = useState<CalibrationStep[]>([
    {
      id: 'setup',
      title: 'Microphone Setup',
      description: 'Test your microphone and adjust settings',
      instruction: 'Please speak normally for 5 seconds to test your microphone.',
      completed: false
    },
    {
      id: 'silence',
      title: 'Background Noise',
      description: 'Measure background noise level',
      instruction: 'Please remain silent for 5 seconds to measure background noise.',
      completed: false
    },
    {
      id: 'range',
      title: 'Voice Range',
      description: 'Determine your vocal range',
      instruction: 'Sing from your lowest comfortable note to your highest note.',
      completed: false
    },
    {
      id: 'volume',
      title: 'Optimal Volume',
      description: 'Find your optimal speaking/singing volume',
      instruction: 'Speak or sing at your normal practice volume.',
      completed: false
    },
    {
      id: 'complete',
      title: 'Calibration Complete',
      description: 'Your voice profile has been created',
      instruction: 'Calibration successful! Your settings have been optimized.',
      completed: false
    }
  ])

  useEffect(() => {
    if (isOpen) {
      initializeAudio()
    }
    return () => {
      cleanup()
    }
  }, [isOpen])

  const initializeAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: false, // We want to measure actual noise
          autoGainControl: false,
          sampleRate: 44100
        }
      })

      mediaStreamRef.current = stream
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream)
      analyserRef.current = audioContextRef.current.createAnalyser()

      analyserRef.current.fftSize = 2048
      analyserRef.current.smoothingTimeConstant = 0.3

      sourceRef.current.connect(analyserRef.current)

    } catch (err: any) {
      setError('Failed to access microphone: ' + err.message)
    }
  }

  const cleanup = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop())
    }
    if (audioContextRef.current) {
      audioContextRef.current.close()
    }
  }

  const startStepCalibration = () => {
    const step = steps[currentStep]
    setIsRecording(true)
    setError(null)

    switch (step.id) {
      case 'setup':
        calibrateMicrophone()
        break
      case 'silence':
        calibrateBackgroundNoise()
        break
      case 'range':
        calibrateVoiceRange()
        break
      case 'volume':
        calibrateOptimalVolume()
        break
    }
  }

  const calibrateMicrophone = () => {
    if (!analyserRef.current) return

    const bufferLength = analyserRef.current.frequencyBinCount
    const dataArray = new Float32Array(bufferLength)
    let samples: number[] = []
    let startTime = Date.now()

    const measure = () => {
      analyserRef.current!.getFloatTimeDomainData(dataArray)

      // Calculate RMS
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i] * dataArray[i]
      }
      const rms = Math.sqrt(sum / dataArray.length)
      samples.push(rms)

      if (Date.now() - startTime < 5000) { // 5 seconds
        animationFrameRef.current = requestAnimationFrame(measure)
      } else {
        // Calculate sensitivity based on average RMS
        const avgRms = samples.reduce((a, b) => a + b) / samples.length
        const sensitivity = Math.min(Math.max(avgRms * 10, 0.1), 1.0)

        setCalibrationData(prev => ({
          ...prev,
          microphoneSensitivity: sensitivity
        }))

        completeStep()
      }
    }

    measure()
  }

  const calibrateBackgroundNoise = () => {
    if (!analyserRef.current) return

    const bufferLength = analyserRef.current.frequencyBinCount
    const dataArray = new Float32Array(bufferLength)
    let samples: number[] = []
    let startTime = Date.now()

    const measure = () => {
      analyserRef.current!.getFloatTimeDomainData(dataArray)

      // Calculate RMS for background noise
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i] * dataArray[i]
      }
      const rms = Math.sqrt(sum / dataArray.length)
      samples.push(rms)

      if (Date.now() - startTime < 5000) { // 5 seconds
        animationFrameRef.current = requestAnimationFrame(measure)
      } else {
        // Calculate background noise level
        const avgNoise = samples.reduce((a, b) => a + b) / samples.length
        const maxNoise = Math.max(...samples)

        setCalibrationData(prev => ({
          ...prev,
          backgroundNoiseLevel: maxNoise
        }))

        completeStep()
      }
    }

    measure()
  }

  const calibrateVoiceRange = () => {
    if (!analyserRef.current) return

    const bufferLength = analyserRef.current.frequencyBinCount
    const dataArray = new Float32Array(bufferLength)
    let pitches: number[] = []
    let startTime = Date.now()

    const measure = () => {
      analyserRef.current!.getFloatTimeDomainData(dataArray)

      // Simple pitch detection using autocorrelation
      const pitch = autoCorrelate(dataArray, audioContextRef.current!.sampleRate)
      if (pitch > 0 && pitch >= 50 && pitch <= 2000) { // Valid human voice range
        pitches.push(pitch)
      }

      if (Date.now() - startTime < 15000) { // 15 seconds for range
        animationFrameRef.current = requestAnimationFrame(measure)
      } else {
        if (pitches.length > 0) {
          const minFreq = Math.min(...pitches)
          const maxFreq = Math.max(...pitches)

          setCalibrationData(prev => ({
            ...prev,
            userVoiceRange: {
              minFrequency: minFreq,
              maxFrequency: maxFreq
            }
          }))
        }

        completeStep()
      }
    }

    measure()
  }

  const calibrateOptimalVolume = () => {
    if (!analyserRef.current) return

    const bufferLength = analyserRef.current.frequencyBinCount
    const dataArray = new Float32Array(bufferLength)
    let volumes: number[] = []
    let startTime = Date.now()

    const measure = () => {
      analyserRef.current!.getFloatTimeDomainData(dataArray)

      // Calculate volume (RMS)
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i] * dataArray[i]
      }
      const volume = Math.sqrt(sum / dataArray.length)
      volumes.push(volume)

      if (Date.now() - startTime < 8000) { // 8 seconds
        animationFrameRef.current = requestAnimationFrame(measure)
      } else {
        // Calculate optimal volume and pitch detection threshold
        const avgVolume = volumes.reduce((a, b) => a + b) / volumes.length
        const backgroundNoise = calibrationData.backgroundNoiseLevel || 0.01

        setCalibrationData(prev => ({
          ...prev,
          optimalVolume: avgVolume,
          pitchDetectionThreshold: backgroundNoise * 2 // Threshold above background noise
        }))

        completeStep()
      }
    }

    measure()
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

    if (rms < 0.01) return -1

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

  const completeStep = () => {
    setIsRecording(false)

    // Mark current step as completed
    setSteps(prev => prev.map((step, index) =>
      index === currentStep ? { ...step, completed: true } : step
    ))

    // Move to next step after a short delay
    setTimeout(() => {
      if (currentStep < steps.length - 1) {
        setCurrentStep(prev => prev + 1)
      } else {
        // All steps complete, create final settings
        const finalSettings: CalibrationSettings = {
          microphoneSensitivity: calibrationData.microphoneSensitivity || 0.5,
          backgroundNoiseLevel: calibrationData.backgroundNoiseLevel || 0.01,
          userVoiceRange: calibrationData.userVoiceRange || { minFrequency: 100, maxFrequency: 800 },
          optimalVolume: calibrationData.optimalVolume || 0.3,
          pitchDetectionThreshold: calibrationData.pitchDetectionThreshold || 0.02
        }

        onCalibrationComplete(finalSettings)
      }
    }, 1000)
  }

  const resetCalibration = () => {
    setCurrentStep(0)
    setCalibrationData({})
    setSteps(prev => prev.map(step => ({ ...step, completed: false })))
    setIsRecording(false)
    setError(null)
  }

  if (!isOpen) return null

  const currentStepData = steps[currentStep]

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Voice Calibration</h2>
              <p className="text-sm text-gray-600">स्वर अंशांकन</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Progress */}
          <div className="px-6 py-4 bg-gray-50">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">
                Step {currentStep + 1} of {steps.length}
              </span>
              <span className="text-sm text-gray-500">
                {Math.round(((currentStep + (currentStepData.completed ? 1 : 0)) / steps.length) * 100)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-orange-500 to-red-500 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${((currentStep + (currentStepData.completed ? 1 : 0)) / steps.length) * 100}%`
                }}
              />
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2 text-red-700">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Current Step */}
          <div className="p-6">
            <div className="text-center mb-6">
              <div className={cn(
                "w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center",
                currentStepData.completed
                  ? "bg-green-100 text-green-600"
                  : isRecording
                  ? "bg-red-100 text-red-600"
                  : "bg-orange-100 text-orange-600"
              )}>
                {currentStepData.completed ? (
                  <CheckCircle className="h-8 w-8" />
                ) : isRecording ? (
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 1, repeat: Infinity }}
                  >
                    <Mic className="h-8 w-8" />
                  </motion.div>
                ) : (
                  <Settings className="h-8 w-8" />
                )}
              </div>

              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {currentStepData.title}
              </h3>
              <p className="text-gray-600 mb-4">
                {currentStepData.description}
              </p>
              <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg">
                {currentStepData.instruction}
              </p>
            </div>

            {/* Step-specific content */}
            {currentStepData.id === 'complete' && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-semibold text-green-800 mb-2">Calibration Results:</h4>
                  <div className="space-y-2 text-sm text-green-700">
                    <div>Microphone Sensitivity: {((calibrationData.microphoneSensitivity || 0) * 100).toFixed(0)}%</div>
                    <div>Background Noise: {((calibrationData.backgroundNoiseLevel || 0) * 100).toFixed(1)}%</div>
                    {calibrationData.userVoiceRange && (
                      <div>
                        Voice Range: {calibrationData.userVoiceRange.minFrequency.toFixed(0)}Hz - {calibrationData.userVoiceRange.maxFrequency.toFixed(0)}Hz
                      </div>
                    )}
                    <div>Optimal Volume: {((calibrationData.optimalVolume || 0) * 100).toFixed(0)}%</div>
                  </div>
                </div>
              </div>
            )}

            {/* Controls */}
            <div className="flex justify-between mt-6">
              {currentStep > 0 && currentStepData.id !== 'complete' && (
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep(prev => prev - 1)}
                >
                  Previous
                </Button>
              )}

              {currentStepData.id === 'complete' ? (
                <div className="flex space-x-2 ml-auto">
                  <Button
                    variant="outline"
                    onClick={resetCalibration}
                  >
                    Recalibrate
                  </Button>
                  <Button
                    variant="carnatic"
                    onClick={onClose}
                  >
                    Done
                  </Button>
                </div>
              ) : (
                <Button
                  variant="carnatic"
                  onClick={startStepCalibration}
                  disabled={isRecording}
                  className="ml-auto"
                >
                  {isRecording ? 'Recording...' : 'Start'}
                </Button>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export { VoiceCalibration }