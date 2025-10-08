import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'

interface Raga {
  id: number
  name: string
  parent_raga?: string
  arohanam: string
  avarohanam: string
  category: 'melakarta' | 'janya'
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  description: string
}

interface RagaSelectorProps {
  selectedRaga?: Raga
  onRagaSelect: (raga: Raga) => void
  difficulty?: 'beginner' | 'intermediate' | 'advanced'
  category?: 'melakarta' | 'janya'
  className?: string
}

const RagaSelector: React.FC<RagaSelectorProps> = ({
  selectedRaga,
  onRagaSelect,
  difficulty,
  category,
  className
}) => {
  const [ragas, setRagas] = useState<Raga[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [filteredRagas, setFilteredRagas] = useState<Raga[]>([])

  useEffect(() => {
    fetchRagas()
  }, [])

  useEffect(() => {
    filterRagas()
  }, [ragas, searchTerm, difficulty, category])

  const fetchRagas = async () => {
    try {
      const response = await fetch('/api/ragas')
      const data = await response.json()
      setRagas(data)
    } catch (error) {
      console.error('Failed to fetch ragas:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterRagas = () => {
    let filtered = ragas

    if (searchTerm) {
      filtered = filtered.filter(raga =>
        raga.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        raga.arohanam.includes(searchTerm) ||
        raga.avarohanam.includes(searchTerm)
      )
    }

    if (difficulty) {
      filtered = filtered.filter(raga => raga.difficulty === difficulty)
    }

    if (category) {
      filtered = filtered.filter(raga => raga.category === category)
    }

    setFilteredRagas(filtered)
  }

  const getDifficultyColor = (level: string) => {
    switch (level) {
      case 'beginner': return 'bg-green-100 text-green-800'
      case 'intermediate': return 'bg-yellow-100 text-yellow-800'
      case 'advanced': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getCategoryColor = (cat: string) => {
    return cat === 'melakarta'
      ? 'bg-purple-100 text-purple-800'
      : 'bg-blue-100 text-blue-800'
  }

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center p-8", className)}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
      </div>
    )
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Search and Filters */}
      <div className="space-y-3">
        <div className="relative">
          <input
            type="text"
            placeholder="Search ragas by name or notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Raga Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredRagas.map((raga) => (
          <motion.div
            key={raga.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className={cn(
              "p-4 rounded-lg border-2 cursor-pointer transition-all duration-200",
              selectedRaga?.id === raga.id
                ? "border-orange-500 bg-orange-50"
                : "border-gray-200 bg-white hover:border-orange-300 hover:bg-orange-25"
            )}
            onClick={() => onRagaSelect(raga)}
          >
            <div className="space-y-3">
              {/* Header */}
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-gray-900">{raga.name}</h3>
                {raga.parent_raga && (
                  <span className="text-xs text-gray-500">
                    from {raga.parent_raga}
                  </span>
                )}
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-2">
                <span className={cn(
                  "px-2 py-1 rounded-full text-xs font-medium",
                  getDifficultyColor(raga.difficulty)
                )}>
                  {raga.difficulty}
                </span>
                <span className={cn(
                  "px-2 py-1 rounded-full text-xs font-medium",
                  getCategoryColor(raga.category)
                )}>
                  {raga.category}
                </span>
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <div className="text-sm">
                  <span className="font-medium text-gray-700">आरोहणम्:</span>
                  <span className="ml-2 text-gray-600">{raga.arohanam}</span>
                </div>
                <div className="text-sm">
                  <span className="font-medium text-gray-700">अवरोहणम्:</span>
                  <span className="ml-2 text-gray-600">{raga.avarohanam}</span>
                </div>
              </div>

              {/* Description */}
              <p className="text-sm text-gray-600 line-clamp-2">
                {raga.description}
              </p>

              {/* Selection Indicator */}
              {selectedRaga?.id === raga.id && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="flex items-center justify-center mt-3"
                >
                  <div className="w-6 h-6 bg-orange-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">✓</span>
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>
        ))}
      </div>

      {/* No Results */}
      {filteredRagas.length === 0 && (
        <div className="text-center py-8">
          <div className="text-gray-500">
            <p className="text-lg font-medium">No ragas found</p>
            <p className="text-sm">Try adjusting your search or filters</p>
          </div>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => {
              setSearchTerm('')
            }}
          >
            Clear Search
          </Button>
        </div>
      )}
    </div>
  )
}

export default RagaSelector