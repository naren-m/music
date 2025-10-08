import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/utils/cn'

interface Tala {
  id: number
  name: string
  pattern: string
  beats_per_cycle: number
  subdivision: string
}

interface TalaVisualizerProps {
  tala: Tala
  currentBeat?: number
  isPlaying?: boolean
  tempo?: number
  onBeatClick?: (beat: number) => void
  showSubdivisions?: boolean
  className?: string
}

const TalaVisualizer: React.FC<TalaVisualizerProps> = ({
  tala,
  currentBeat = 0,
  isPlaying = false,
  tempo = 120,
  onBeatClick,
  showSubdivisions = true,
  className
}) => {
  const [internalBeat, setInternalBeat] = useState(0)

  useEffect(() => {
    if (isPlaying) {
      const interval = setInterval(() => {
        setInternalBeat(prev => (prev + 1) % tala.beats_per_cycle)
      }, (60 / tempo) * 1000)

      return () => clearInterval(interval)
    }
  }, [isPlaying, tempo, tala.beats_per_cycle])

  const activeBeat = currentBeat >= 0 ? currentBeat : internalBeat

  const parsePattern = (pattern: string) => {
    const symbols = pattern.split('')
    return symbols.map((symbol, index) => ({
      symbol,
      beat: index,
      type: getTalaType(symbol)
    }))
  }

  const getTalaType = (symbol: string): 'sam' | 'tali' | 'khali' | 'subdivision' => {
    switch (symbol) {
      case 'X': return 'sam' // Sam (first beat)
      case '2':
      case '3':
      case '4': return 'tali' // Tali (clapped beats)
      case '0': return 'khali' // Khali (waved beats)
      default: return 'subdivision'
    }
  }

  const getSymbolColor = (type: string, isActive: boolean) => {
    const baseColors = {
      sam: 'border-red-500 bg-red-50 text-red-700',
      tali: 'border-green-500 bg-green-50 text-green-700',
      khali: 'border-blue-500 bg-blue-50 text-blue-700',
      subdivision: 'border-gray-300 bg-gray-50 text-gray-700'
    }

    const activeColors = {
      sam: 'border-red-600 bg-red-100 text-red-800 shadow-lg scale-110',
      tali: 'border-green-600 bg-green-100 text-green-800 shadow-lg scale-110',
      khali: 'border-blue-600 bg-blue-100 text-blue-800 shadow-lg scale-110',
      subdivision: 'border-gray-400 bg-gray-100 text-gray-800 shadow-md scale-105'
    }

    return isActive ? activeColors[type] : baseColors[type]
  }

  const getSymbolDevanagari = (symbol: string) => {
    const devanagariMap = {
      'X': 'सम्',
      '2': '२',
      '3': '३',
      '4': '४',
      '0': '०'
    }
    return devanagariMap[symbol] || symbol
  }

  const patternElements = parsePattern(tala.pattern)

  return (
    <div className={cn("space-y-6", className)}>
      {/* Tala Info */}
      <div className="text-center space-y-2">
        <h3 className="text-2xl font-bold text-gray-900">{tala.name}</h3>
        <div className="flex items-center justify-center space-x-4 text-sm text-gray-600">
          <span>{tala.beats_per_cycle} beats</span>
          <span>•</span>
          <span>{tempo} BPM</span>
          {isPlaying && (
            <>
              <span>•</span>
              <motion.span
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ duration: 0.6, repeat: Infinity }}
                className="text-green-600 font-medium"
              >
                Playing
              </motion.span>
            </>
          )}
        </div>
      </div>

      {/* Main Tala Pattern */}
      <div className="flex items-center justify-center">
        <div className="flex space-x-2 p-4 rounded-lg bg-gray-50">
          {patternElements.map((element, index) => (
            <motion.button
              key={index}
              className={cn(
                "w-16 h-16 rounded-full border-2 flex flex-col items-center justify-center transition-all duration-200 font-bold text-lg",
                getSymbolColor(element.type, index === activeBeat),
                onBeatClick && "cursor-pointer hover:shadow-md"
              )}
              onClick={() => onBeatClick?.(index)}
              whileHover={onBeatClick ? { scale: 1.05 } : {}}
              whileTap={onBeatClick ? { scale: 0.95 } : {}}
              animate={index === activeBeat ? {
                scale: [1, 1.1, 1],
                transition: { duration: 0.3 }
              } : {}}
            >
              <span className="text-xs opacity-75">{getSymbolDevanagari(element.symbol)}</span>
              <span>{element.symbol}</span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Beat Counter */}
      <div className="text-center">
        <div className="inline-flex items-center space-x-2 px-4 py-2 bg-white border rounded-full shadow-sm">
          <span className="text-sm text-gray-600">Beat:</span>
          <motion.span
            key={activeBeat}
            initial={{ scale: 1.5, color: '#f97316' }}
            animate={{ scale: 1, color: '#374151' }}
            className="text-lg font-bold"
          >
            {activeBeat + 1}
          </motion.span>
          <span className="text-sm text-gray-600">of {tala.beats_per_cycle}</span>
        </div>
      </div>

      {/* Subdivisions */}
      {showSubdivisions && tala.subdivision && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="space-y-3"
        >
          <div className="text-center">
            <h4 className="text-sm font-medium text-gray-700">Subdivisions</h4>
          </div>

          <div className="grid grid-cols-8 gap-1 max-w-md mx-auto">
            {Array.from({ length: tala.beats_per_cycle * 4 }).map((_, index) => {
              const beatIndex = Math.floor(index / 4)
              const subdivisionIndex = index % 4
              const isMainBeat = subdivisionIndex === 0
              const isActive = beatIndex === activeBeat

              return (
                <motion.div
                  key={index}
                  className={cn(
                    "h-3 rounded-full transition-all duration-200",
                    isMainBeat
                      ? isActive
                        ? "bg-orange-500"
                        : "bg-gray-400"
                      : isActive
                        ? "bg-orange-300"
                        : "bg-gray-200"
                  )}
                  animate={isActive ? {
                    scale: [1, 1.2, 1],
                    transition: { duration: 0.15, delay: subdivisionIndex * 0.05 }
                  } : {}}
                />
              )
            })}
          </div>
        </motion.div>
      )}

      {/* Tala Pattern Key */}
      <div className="text-center space-y-2">
        <h4 className="text-sm font-medium text-gray-700">Pattern Key</h4>
        <div className="flex items-center justify-center space-x-4 text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-4 h-4 rounded-full border-2 border-red-500 bg-red-50"></div>
            <span>Sam (X)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-4 rounded-full border-2 border-green-500 bg-green-50"></div>
            <span>Tali (2,3,4)</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-4 rounded-full border-2 border-blue-500 bg-blue-50"></div>
            <span>Khali (0)</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TalaVisualizer