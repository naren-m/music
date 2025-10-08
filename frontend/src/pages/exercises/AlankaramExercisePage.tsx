import React from 'react'
import { AlankaramInterface } from '../../components/exercises/alankaram/AlankaramInterface'

const AlankaramExercisePage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="carnatic-card p-6">
        <h1 className="text-3xl font-bold text-saffron-400 mb-2">
          Alankaram • अलंकारम्
        </h1>
        <p className="text-gray-300 text-lg mb-4">
          Ornamental patterns that beautify and enhance melodic expression
        </p>

        {/* Cultural Context */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h3 className="font-semibold text-white mb-2">Cultural Significance</h3>
          <p className="text-gray-400 text-sm">
            Alankaram (ornamental patterns) are the third fundamental exercise type in Carnatic music.
            The word "Alankaram" means decoration or ornamentation. These 35 traditional patterns
            introduce students to the concept of gamakas (ornaments) and develop the flexibility
            required for advanced Carnatic music performance. Each pattern has specific cultural
            and pedagogical significance in the traditional learning system.
          </p>
        </div>
      </div>

      {/* Exercise Interface */}
      <div className="carnatic-card">
        <AlankaramInterface />
      </div>

      {/* Pattern Categories */}
      <div className="carnatic-card p-6">
        <h3 className="text-xl font-semibold text-white mb-4">Traditional Pattern Categories</h3>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="bg-slate-700/30 rounded-lg p-4">
            <h4 className="font-medium text-green-400 mb-2">Simple Patterns (1-12)</h4>
            <p className="text-gray-400 text-sm mb-2">
              Basic ornamental movements introducing melodic curves and simple gamakas.
            </p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>• Linear ornamental movements</li>
              <li>• Basic melodic curves</li>
              <li>• Foundation for complex patterns</li>
            </ul>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-4">
            <h4 className="font-medium text-blue-400 mb-2">Compound Patterns (13-24)</h4>
            <p className="text-gray-400 text-sm mb-2">
              Intermediate patterns with multiple ornamental elements and rhythmic variations.
            </p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>• Multiple gamaka combinations</li>
              <li>• Rhythmic complexity</li>
              <li>• Raga-specific adaptations</li>
            </ul>
          </div>
          <div className="bg-slate-700/30 rounded-lg p-4">
            <h4 className="font-medium text-orange-400 mb-2">Complex Patterns (25-35)</h4>
            <p className="text-gray-400 text-sm mb-2">
              Advanced ornamental patterns preparing for performance-level expression.
            </p>
            <ul className="text-xs text-gray-500 space-y-1">
              <li>• Advanced gamaka techniques</li>
              <li>• Performance-ready ornaments</li>
              <li>• Artistic expression development</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Advanced Practice Tips */}
      <div className="carnatic-card p-6">
        <h3 className="text-xl font-semibold text-white mb-4">Advanced Practice Techniques</h3>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-saffron-400 mb-2">Ornamentation Mastery:</h4>
            <ul className="space-y-1 text-gray-400 text-sm">
              <li>• Study each pattern's cultural significance</li>
              <li>• Practice with different raga adaptations</li>
              <li>• Focus on smooth gamaka execution</li>
              <li>• Develop personal artistic expression</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-saffron-400 mb-2">Raga Integration:</h4>
            <ul className="space-y-1 text-gray-400 text-sm">
              <li>• Practice patterns in different ragas</li>
              <li>• Learn raga-specific microtonal adjustments</li>
              <li>• Understand emotional context of each raga</li>
              <li>• Develop improvisational skills</li>
            </ul>
          </div>
        </div>

        {/* Progression Path */}
        <div className="mt-6 bg-slate-700/20 rounded-lg p-4">
          <h4 className="font-medium text-white mb-2">Learning Progression:</h4>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="bg-green-600/20 text-green-400 px-2 py-1 rounded">1. Master basic patterns (1-12)</span>
            <span className="bg-blue-600/20 text-blue-400 px-2 py-1 rounded">2. Develop compound techniques (13-24)</span>
            <span className="bg-orange-600/20 text-orange-400 px-2 py-1 rounded">3. Achieve artistic mastery (25-35)</span>
            <span className="bg-purple-600/20 text-purple-400 px-2 py-1 rounded">4. Apply to compositions</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AlankaramExercisePage