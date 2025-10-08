import React from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, Music, Sparkles } from 'lucide-react'

const ExercisesPage: React.FC = () => {
  const exercises = [
    {
      id: 'sarali',
      title: 'Sarali Varisai',
      titleDevanagari: 'सरळी वरिसै',
      description: 'Foundation exercises with ascending and descending patterns',
      culturalContext: 'Basic melodic exercises that form the foundation of Carnatic music',
      level: 'Beginner',
      duration: '15-30 minutes',
      patterns: 12,
      icon: Music,
      color: 'from-blue-600 to-purple-600',
      href: '/exercises/sarali'
    },
    {
      id: 'janta',
      title: 'Janta Varisai',
      titleDevanagari: 'जंत वरिसै',
      description: 'Double-note exercises with transition patterns',
      culturalContext: 'Exercises focusing on smooth transitions between pairs of notes',
      level: 'Intermediate',
      duration: '20-40 minutes',
      patterns: 8,
      icon: BookOpen,
      color: 'from-green-600 to-teal-600',
      href: '/exercises/janta'
    },
    {
      id: 'alankaram',
      title: 'Alankaram',
      titleDevanagari: 'अलंकारम्',
      description: 'Ornamental patterns with raga-specific variations',
      culturalContext: 'Advanced ornamental exercises with 35 traditional patterns',
      level: 'Advanced',
      duration: '30-60 minutes',
      patterns: 35,
      icon: Sparkles,
      color: 'from-orange-600 to-red-600',
      href: '/exercises/alankaram'
    }
  ]

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-saffron-400 to-deepOrange-400 bg-clip-text text-transparent mb-4">
          अभ्यास • Practice Exercises
        </h1>
        <p className="text-xl text-gray-400 max-w-3xl mx-auto">
          Master the fundamentals of Carnatic music through traditional exercises,
          enhanced with modern technology for real-time feedback and progress tracking.
        </p>
      </div>

      {/* Cultural Context */}
      <div className="carnatic-card p-6">
        <h2 className="text-2xl font-semibold text-saffron-400 mb-4">Traditional Learning Path</h2>
        <p className="text-gray-300 leading-relaxed mb-4">
          The traditional Carnatic music education system follows a structured progression through three main types of exercises.
          Each builds upon the previous, developing technique, intonation, and musical expression.
        </p>
        <div className="grid md:grid-cols-3 gap-4 text-center">
          <div className="p-4 bg-slate-700/30 rounded-lg">
            <h3 className="font-semibold text-blue-400 mb-2">Foundation</h3>
            <p className="text-sm text-gray-400">Sarali Varisai builds basic melodic movement</p>
          </div>
          <div className="p-4 bg-slate-700/30 rounded-lg">
            <h3 className="font-semibold text-green-400 mb-2">Development</h3>
            <p className="text-sm text-gray-400">Janta Varisai develops smooth transitions</p>
          </div>
          <div className="p-4 bg-slate-700/30 rounded-lg">
            <h3 className="font-semibold text-orange-400 mb-2">Mastery</h3>
            <p className="text-sm text-gray-400">Alankaram introduces ornamental patterns</p>
          </div>
        </div>
      </div>

      {/* Exercise Cards */}
      <div className="grid lg:grid-cols-3 gap-8">
        {exercises.map((exercise) => {
          const IconComponent = exercise.icon
          return (
            <Link
              key={exercise.id}
              to={exercise.href}
              className="group block"
            >
              <div className={`bg-gradient-to-br ${exercise.color} rounded-xl p-6 text-white transition-all duration-300 group-hover:scale-105 group-hover:shadow-2xl`}>
                <div className="flex items-center justify-between mb-6">
                  <IconComponent className="h-10 w-10" />
                  <div className="text-right">
                    <div className="text-sm opacity-80">Level</div>
                    <div className="font-bold">{exercise.level}</div>
                  </div>
                </div>

                <h2 className="text-2xl font-bold mb-2">{exercise.title}</h2>
                <p className="text-lg font-devanagari opacity-90 mb-4">{exercise.titleDevanagari}</p>
                <p className="opacity-90 mb-4">{exercise.description}</p>

                <div className="space-y-3 mb-6">
                  <div className="flex justify-between text-sm">
                    <span>Duration:</span>
                    <span className="font-semibold">{exercise.duration}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Patterns:</span>
                    <span className="font-semibold">{exercise.patterns}</span>
                  </div>
                </div>

                <div className="border-t border-white/20 pt-4">
                  <p className="text-sm opacity-75 italic">
                    "{exercise.culturalContext}"
                  </p>
                </div>

                <div className="mt-6 flex items-center justify-between">
                  <span className="text-sm font-semibold">Start Practice →</span>
                  <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center group-hover:bg-white/30 transition-colors">
                    <IconComponent className="h-5 w-5" />
                  </div>
                </div>
              </div>
            </Link>
          )
        })}
      </div>

      {/* Practice Tips */}
      <div className="carnatic-card p-6">
        <h2 className="text-2xl font-semibold text-saffron-400 mb-4">Practice Guidelines</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-white mb-3">Before You Begin:</h3>
            <ul className="space-y-2 text-gray-300">
              <li>• Complete voice calibration for accurate pitch detection</li>
              <li>• Ensure quiet environment for best recording quality</li>
              <li>• Set comfortable tempo and gradually increase speed</li>
              <li>• Practice with proper posture and breathing</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-white mb-3">During Practice:</h3>
            <ul className="space-y-2 text-gray-300">
              <li>• Focus on accuracy over speed initially</li>
              <li>• Pay attention to real-time pitch feedback</li>
              <li>• Record sessions for later review and analysis</li>
              <li>• Take breaks to prevent vocal fatigue</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ExercisesPage