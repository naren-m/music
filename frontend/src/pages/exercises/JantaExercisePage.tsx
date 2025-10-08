import React from 'react'
import { JantaInterface } from '../../components/exercises/janta/JantaInterface'

const JantaExercisePage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="carnatic-card p-6">
        <h1 className="text-3xl font-bold text-saffron-400 mb-2">
          Janta Varisai • जंत वरिसै
        </h1>
        <p className="text-gray-300 text-lg mb-4">
          Double-note exercises focusing on smooth transitions and rhythmic precision
        </p>

        {/* Cultural Context */}
        <div className="bg-slate-700/30 rounded-lg p-4">
          <h3 className="font-semibold text-white mb-2">Cultural Significance</h3>
          <p className="text-gray-400 text-sm">
            Janta Varisai introduce the concept of double notes, where each swara is sung twice.
            This develops precision in note transitions, rhythmic stability, and prepares students
            for complex ornamental patterns. The term "Janta" refers to pairs or couples,
            emphasizing the paired nature of these exercises.
          </p>
        </div>
      </div>

      {/* Exercise Interface */}
      <div className="carnatic-card">
        <JantaInterface />
      </div>

      {/* Practice Guidelines */}
      <div className="carnatic-card p-6">
        <h3 className="text-xl font-semibold text-white mb-4">Practice Guidelines</h3>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-saffron-400 mb-2">Double Note Technique:</h4>
            <ul className="space-y-1 text-gray-400 text-sm">
              <li>• Maintain equal duration for both notes</li>
              <li>• Practice smooth transitions between pairs</li>
              <li>• Focus on clear articulation of each note</li>
              <li>• Develop consistent emphasis patterns</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-saffron-400 mb-2">Rhythmic Development:</h4>
            <ul className="space-y-1 text-gray-400 text-sm">
              <li>• Start with slower tempo for accuracy</li>
              <li>• Practice with metronome for stability</li>
              <li>• Gradually increase speed while maintaining quality</li>
              <li>• Record and analyze transition smoothness</li>
            </ul>
          </div>
        </div>

        {/* Difficulty Progression */}
        <div className="mt-6">
          <h4 className="font-medium text-saffron-400 mb-3">Difficulty Levels:</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
            <div className="bg-slate-700/30 rounded p-3">
              <div className="font-medium text-green-400">Level 1-2</div>
              <div className="text-gray-400">Basic double notes</div>
            </div>
            <div className="bg-slate-700/30 rounded p-3">
              <div className="font-medium text-blue-400">Level 3-4</div>
              <div className="text-gray-400">Variable emphasis</div>
            </div>
            <div className="bg-slate-700/30 rounded p-3">
              <div className="font-medium text-orange-400">Level 5-6</div>
              <div className="text-gray-400">Complex transitions</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default JantaExercisePage