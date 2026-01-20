import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/utils/cn'

interface SwaraWheelProps {
  currentSwara?: string
  targetSwara?: string
  centDeviation?: number
  confidence?: number
  interactive?: boolean
  onSwaraSelect?: (swara: string) => void
  className?: string
}

const SWARAS = [
  { name: 'Sa', position: 0, color: '#FF6B35', symbol: 'स' },
  { name: 'Ri', position: 1, color: '#FF8555', symbol: 'रि' },
  { name: 'Ga', position: 2, color: '#FFA075', symbol: 'ग' },
  { name: 'Ma', position: 3, color: '#FFB895', symbol: 'म' },
  { name: 'Pa', position: 4, color: '#FFD0B5', symbol: 'प' },
  { name: 'Da', position: 5, color: '#FFE8D5', symbol: 'ध' },
  { name: 'Ni', position: 6, color: '#FFF5F0', symbol: 'नि' }
]

const SwaraWheel: React.FC<SwaraWheelProps> = ({
  currentSwara,
  targetSwara,
  centDeviation = 0,
  confidence = 0,
  interactive = false,
  onSwaraSelect,
  className
}) => {
  const [selectedSwara, setSelectedSwara] = useState<string | null>(null)
  const [rotation, setRotation] = useState(0)
  const wheelRef = useRef<SVGSVGElement>(null)

  // Rotate wheel to highlight current swara
  useEffect(() => {
    if (currentSwara) {
      const swaraIndex = SWARAS.findIndex(s => s.name === currentSwara)
      if (swaraIndex !== -1) {
        const targetRotation = -swaraIndex * (360 / SWARAS.length)
        setRotation(targetRotation)
      }
    }
  }, [currentSwara])

  const handleSwaraClick = (swara: string) => {
    if (interactive) {
      setSelectedSwara(swara)
      onSwaraSelect?.(swara)
    }
  }

  const getCentDeviationColor = (cents: number) => {
    const absDeviation = Math.abs(cents)
    if (absDeviation < 10) return '#4ADE80' // Green - very accurate
    if (absDeviation < 25) return '#FBD38D' // Yellow - acceptable
    if (absDeviation < 50) return '#F6AD55' // Orange - needs work
    return '#FC8181' // Red - poor
  }

  const getConfidenceOpacity = (conf: number) => {
    return Math.max(0.3, Math.min(1, conf))
  }

  return (
    <div className={cn("relative flex items-center justify-center", className)}>
      {/* Main Swara Wheel */}
      <motion.svg
        ref={wheelRef}
        width="300"
        height="300"
        viewBox="0 0 300 300"
        className="drop-shadow-lg"
        animate={{ rotate: rotation }}
        transition={{ type: "spring", stiffness: 100, damping: 20 }}
      >
        {/* Background circle */}
        <circle
          cx="150"
          cy="150"
          r="140"
          fill="url(#wheelGradient)"
          stroke="#1F2937"
          strokeWidth="2"
        />

        {/* Gradient definitions */}
        <defs>
          <radialGradient id="wheelGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#FFF7ED" />
            <stop offset="100%" stopColor="#FDBA74" />
          </radialGradient>

          <radialGradient id="centerGradient" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="100%" stopColor="#F3F4F6" />
          </radialGradient>
        </defs>

        {/* Swara segments */}
        {SWARAS.map((swara, index) => {
          const angle = (index * 360) / SWARAS.length
          const startAngle = angle - (360 / SWARAS.length) / 2
          const endAngle = angle + (360 / SWARAS.length) / 2

          const isActive = currentSwara === swara.name
          const isTarget = targetSwara === swara.name
          const isSelected = selectedSwara === swara.name

          // Calculate path for swara segment
          const outerRadius = 140
          const innerRadius = 60

          const startAngleRad = (startAngle * Math.PI) / 180
          const endAngleRad = (endAngle * Math.PI) / 180

          const x1 = 150 + outerRadius * Math.cos(startAngleRad)
          const y1 = 150 + outerRadius * Math.sin(startAngleRad)
          const x2 = 150 + outerRadius * Math.cos(endAngleRad)
          const y2 = 150 + outerRadius * Math.sin(endAngleRad)
          const x3 = 150 + innerRadius * Math.cos(endAngleRad)
          const y3 = 150 + innerRadius * Math.sin(endAngleRad)
          const x4 = 150 + innerRadius * Math.cos(startAngleRad)
          const y4 = 150 + innerRadius * Math.sin(startAngleRad)

          const pathData = `M ${x1} ${y1} A ${outerRadius} ${outerRadius} 0 0 1 ${x2} ${y2} L ${x3} ${y3} A ${innerRadius} ${innerRadius} 0 0 0 ${x4} ${y4} Z`

          // Text position (middle of the segment)
          const textRadius = (outerRadius + innerRadius) / 2
          const textAngle = angle
          const textX = 150 + textRadius * Math.cos((textAngle * Math.PI) / 180)
          const textY = 150 + textRadius * Math.sin((textAngle * Math.PI) / 180)

          return (
            <g key={swara.name}>
              {/* Swara segment */}
              <path
                d={pathData}
                fill={swara.color}
                stroke="#1F2937"
                strokeWidth="1"
                opacity={
                  isActive ? getConfidenceOpacity(confidence) :
                  isTarget ? 0.8 :
                  isSelected ? 0.9 : 0.6
                }
                className={cn(
                  "transition-all duration-200",
                  interactive && "cursor-pointer hover:opacity-90"
                )}
                onClick={() => handleSwaraClick(swara.name)}
              />

              {/* Active swara highlight */}
              {isActive && (
                <path
                  d={pathData}
                  fill="none"
                  stroke={getCentDeviationColor(centDeviation)}
                  strokeWidth="4"
                  opacity="0.8"
                />
              )}

              {/* Target swara indicator */}
              {isTarget && (
                <path
                  d={pathData}
                  fill="none"
                  stroke="#10B981"
                  strokeWidth="3"
                  strokeDasharray="5,5"
                  opacity="0.9"
                />
              )}

              {/* Swara name */}
              <text
                x={textX}
                y={textY}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="16"
                fontWeight="bold"
                fill="#1F2937"
                className="select-none"
              >
                {swara.name}
              </text>

              {/* Devanagari symbol */}
              <text
                x={textX}
                y={textY + 16}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="12"
                fill="#6B7280"
                className="select-none"
              >
                {swara.symbol}
              </text>
            </g>
          )
        })}

        {/* Center circle */}
        <circle
          cx="150"
          cy="150"
          r="50"
          fill="url(#centerGradient)"
          stroke="#1F2937"
          strokeWidth="2"
        />

        {/* Center text */}
        <text
          x="150"
          y="145"
          textAnchor="middle"
          dominantBaseline="central"
          fontSize="12"
          fontWeight="bold"
          fill="#1F2937"
          className="select-none"
        >
          सप्त स्वर
        </text>
        <text
          x="150"
          y="160"
          textAnchor="middle"
          dominantBaseline="central"
          fontSize="10"
          fill="#6B7280"
          className="select-none"
        >
          Seven Notes
        </text>
      </motion.svg>

      {/* Confidence indicator */}
      {currentSwara && confidence > 0 && (
        <motion.div
          key="confidence-indicator"
          className="absolute top-0 right-0 bg-white rounded-full p-2 shadow-lg border"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 300 }}
        >
          <div className="text-xs font-semibold text-center">
            <div className="text-gray-600">Confidence</div>
            <div
              className="text-lg font-bold"
              style={{ color: getCentDeviationColor(centDeviation) }}
            >
              {Math.round(confidence * 100)}%
            </div>
          </div>
        </motion.div>
      )}

      {/* Cent deviation indicator */}
      {currentSwara && Math.abs(centDeviation) > 0 && (
        <motion.div
          key="cent-deviation-indicator"
          className="absolute bottom-0 left-0 bg-white rounded-full p-2 shadow-lg border"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 300, delay: 0.1 }}
        >
          <div className="text-xs font-semibold text-center">
            <div className="text-gray-600">Deviation</div>
            <div
              className="text-sm font-bold"
              style={{ color: getCentDeviationColor(centDeviation) }}
            >
              {centDeviation > 0 ? '+' : ''}{Math.round(centDeviation)}¢
            </div>
          </div>
        </motion.div>
      )}

      {/* Practice mode indicator */}
      {targetSwara && targetSwara !== currentSwara && (
        <motion.div
          key="target-swara-indicator"
          className="absolute top-0 left-0 bg-green-100 border border-green-300 rounded-full p-2 shadow-lg"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 300, delay: 0.2 }}
        >
          <div className="text-xs font-semibold text-center text-green-700">
            <div>Target</div>
            <div className="text-sm font-bold">{targetSwara}</div>
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default SwaraWheel