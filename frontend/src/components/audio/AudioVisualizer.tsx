import React, { useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/utils/cn'

interface AudioVisualizerProps {
  audioData?: Float32Array | null
  frequencyData?: Uint8Array | null
  isRecording?: boolean
  currentPitch?: {
    frequency: number
    note: string
    confidence: number
  } | null
  referenceFrequency?: number
  className?: string
  visualizationType?: 'waveform' | 'spectrum' | 'pitch'
}

const AudioVisualizer: React.FC<AudioVisualizerProps> = ({
  audioData,
  frequencyData,
  isRecording = false,
  currentPitch,
  referenceFrequency = 261.63,
  className,
  visualizationType = 'waveform'
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationFrameRef = useRef<number>()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width * window.devicePixelRatio
      canvas.height = rect.height * window.devicePixelRatio
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    return () => {
      window.removeEventListener('resize', resizeCanvas)
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [])

  useEffect(() => {
    if (!isRecording) return

    const animate = () => {
      draw()
      animationFrameRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [audioData, frequencyData, isRecording, currentPitch, visualizationType])

  const draw = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const rect = canvas.getBoundingClientRect()
    const width = rect.width
    const height = rect.height

    // Clear canvas
    ctx.clearRect(0, 0, width, height)

    // Set background gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, height)
    gradient.addColorStop(0, 'rgba(249, 115, 22, 0.1)') // orange-500 with opacity
    gradient.addColorStop(1, 'rgba(239, 68, 68, 0.1)')  // red-500 with opacity
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, width, height)

    if (visualizationType === 'waveform' && audioData) {
      drawWaveform(ctx, audioData, width, height)
    } else if (visualizationType === 'spectrum' && frequencyData) {
      drawSpectrum(ctx, frequencyData, width, height)
    } else if (visualizationType === 'pitch' && currentPitch) {
      drawPitchVisualization(ctx, currentPitch, width, height)
    }
  }

  const drawWaveform = (ctx: CanvasRenderingContext2D, data: Float32Array, width: number, height: number) => {
    const centerY = height / 2
    const sliceWidth = width / data.length

    ctx.lineWidth = 2
    ctx.strokeStyle = 'rgba(249, 115, 22, 0.8)' // orange-500

    ctx.beginPath()
    ctx.moveTo(0, centerY)

    for (let i = 0; i < data.length; i++) {
      const x = i * sliceWidth
      const y = centerY + (data[i] * centerY * 0.8) // Scale to 80% of half height

      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    }

    ctx.stroke()

    // Add glow effect
    ctx.shadowBlur = 10
    ctx.shadowColor = 'rgba(249, 115, 22, 0.5)'
    ctx.stroke()
    ctx.shadowBlur = 0
  }

  const drawSpectrum = (ctx: CanvasRenderingContext2D, data: Uint8Array, width: number, height: number) => {
    const barWidth = width / data.length * 2
    const barSpacing = 1

    for (let i = 0; i < data.length / 2; i++) {
      const barHeight = (data[i] / 255) * height * 0.8
      const x = i * (barWidth + barSpacing)
      const y = height - barHeight

      // Create gradient for each bar
      const gradient = ctx.createLinearGradient(0, y, 0, height)
      gradient.addColorStop(0, 'rgba(249, 115, 22, 0.9)') // orange-500
      gradient.addColorStop(0.5, 'rgba(251, 146, 60, 0.7)') // orange-400
      gradient.addColorStop(1, 'rgba(239, 68, 68, 0.5)')   // red-500

      ctx.fillStyle = gradient
      ctx.fillRect(x, y, barWidth, barHeight)
    }
  }

  const drawPitchVisualization = (
    ctx: CanvasRenderingContext2D,
    pitch: { frequency: number; note: string; confidence: number },
    width: number,
    height: number
  ) => {
    const centerY = height / 2
    const centerX = width / 2

    // Draw reference line
    ctx.strokeStyle = 'rgba(156, 163, 175, 0.5)' // gray-400
    ctx.lineWidth = 1
    ctx.setLineDash([5, 5])
    ctx.beginPath()
    ctx.moveTo(0, centerY)
    ctx.lineTo(width, centerY)
    ctx.stroke()
    ctx.setLineDash([])

    // Calculate pitch deviation from reference
    const cents = 1200 * Math.log2(pitch.frequency / referenceFrequency)
    const maxCents = 100 // ±100 cents range
    const deviationY = centerY - (cents / maxCents) * (height * 0.4)

    // Draw current pitch indicator
    const radius = 8 + (pitch.confidence * 12) // Size based on confidence
    const alpha = 0.3 + (pitch.confidence * 0.7) // Opacity based on confidence

    ctx.fillStyle = `rgba(249, 115, 22, ${alpha})` // orange-500 with variable opacity
    ctx.beginPath()
    ctx.arc(centerX, Math.max(radius, Math.min(height - radius, deviationY)), radius, 0, 2 * Math.PI)
    ctx.fill()

    // Draw pitch trail
    ctx.strokeStyle = `rgba(249, 115, 22, 0.3)`
    ctx.lineWidth = 3
    ctx.beginPath()
    ctx.arc(centerX, Math.max(radius, Math.min(height - radius, deviationY)), radius + 5, 0, 2 * Math.PI)
    ctx.stroke()

    // Draw pitch information
    ctx.fillStyle = 'rgba(55, 65, 81, 0.9)' // gray-700
    ctx.font = '16px system-ui, -apple-system, sans-serif'
    ctx.textAlign = 'center'

    const noteText = pitch.note
    const freqText = `${pitch.frequency.toFixed(1)} Hz`
    const confidenceText = `${(pitch.confidence * 100).toFixed(0)}%`

    ctx.fillText(noteText, centerX, 30)
    ctx.fillText(freqText, centerX, 50)
    ctx.fillText(confidenceText, centerX, height - 20)

    // Draw cent deviation indicator
    if (Math.abs(cents) > 5) { // Only show if significantly off
      const centsText = `${cents > 0 ? '+' : ''}${cents.toFixed(0)}¢`
      ctx.fillStyle = cents > 0 ? 'rgba(239, 68, 68, 0.8)' : 'rgba(59, 130, 246, 0.8)'
      ctx.fillText(centsText, centerX, 70)
    }
  }

  return (
    <div className={cn("relative bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border overflow-hidden", className)}>
      {/* Canvas */}
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        style={{ display: 'block' }}
      />

      {/* Visualization Type Selector */}
      <div className="absolute top-2 right-2 flex space-x-1">
        {['waveform', 'spectrum', 'pitch'].map((type) => (
          <button
            key={type}
            onClick={() => {/* Toggle visualization type */}}
            className={cn(
              "px-2 py-1 text-xs rounded transition-colors",
              visualizationType === type
                ? "bg-orange-500 text-white"
                : "bg-white/80 text-gray-600 hover:bg-white"
            )}
          >
            {type}
          </button>
        ))}
      </div>

      {/* Recording Indicator */}
      {isRecording && (
        <motion.div
          animate={{ opacity: [1, 0.3, 1] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="absolute top-2 left-2 flex items-center space-x-2 px-2 py-1 bg-red-500 text-white text-xs rounded-full"
        >
          <div className="w-2 h-2 bg-white rounded-full" />
          <span>RECORDING</span>
        </motion.div>
      )}

      {/* Status Overlay */}
      {!isRecording && !audioData && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <div className="w-12 h-12 mx-auto mb-2 rounded-full bg-gray-200 flex items-center justify-center">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
            </div>
            <p className="text-sm">Start recording to see audio visualization</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default AudioVisualizer