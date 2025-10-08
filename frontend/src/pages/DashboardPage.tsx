import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { usePracticeSession } from '../contexts/PracticeSessionContext'
import { BookOpen, Mic, BarChart3, Settings } from 'lucide-react'

const DashboardPage: React.FC = () => {
  const { user } = useAuth()
  const { stats } = usePracticeSession()

  const quickActions = [
    {
      title: 'Practice Exercises',
      titleDevanagari: 'अभ्यास',
      description: 'Continue your daily practice',
      icon: BookOpen,
      href: '/exercises',
      color: 'from-blue-600 to-purple-600'
    },
    {
      title: 'Voice Recording',
      titleDevanagari: 'स्वर रिकॉर्डिंग',
      description: 'Record and analyze your voice',
      icon: Mic,
      href: '/recording',
      color: 'from-green-600 to-teal-600'
    },
    {
      title: 'Progress Analytics',
      titleDevanagari: 'प्रगति विश्लेषण',
      description: 'View your learning progress',
      icon: BarChart3,
      href: '/analytics',
      color: 'from-orange-600 to-red-600'
    },
    {
      title: 'Settings',
      titleDevanagari: 'सेटिंग्स',
      description: 'Customize your learning experience',
      icon: Settings,
      href: '/settings',
      color: 'from-purple-600 to-pink-600'
    }
  ]

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-saffron-600 to-deepOrange-600 rounded-xl p-6 text-white">
        <h1 className="text-3xl font-bold mb-2">
          Welcome back, {user?.name || 'Student'}! 🎵
        </h1>
        <p className="text-orange-100 text-lg">
          Continue your journey in Carnatic music learning
        </p>
        <div className="mt-4 flex items-center space-x-6 text-orange-100">
          <div className="flex items-center space-x-2">
            <span className="font-semibold">{stats?.totalSessions || 0}</span>
            <span>Sessions</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="font-semibold">{stats?.currentStreak || 0}</span>
            <span>Day Streak</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="font-semibold">{Math.round((stats?.totalPracticeTime || 0) / 60)}m</span>
            <span>Total Practice</span>
          </div>
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {quickActions.map((action) => {
          const IconComponent = action.icon
          return (
            <Link
              key={action.title}
              to={action.href}
              className="group block"
            >
              <div className={`bg-gradient-to-br ${action.color} rounded-xl p-6 text-white transition-all duration-200 group-hover:scale-105 group-hover:shadow-xl`}>
                <div className="flex items-center justify-between mb-4">
                  <IconComponent className="h-8 w-8" />
                  <div className="opacity-20 group-hover:opacity-30 transition-opacity">
                    <IconComponent className="h-16 w-16" />
                  </div>
                </div>
                <h3 className="text-xl font-semibold mb-1">{action.title}</h3>
                <p className="text-sm font-devanagari opacity-80 mb-2">{action.titleDevanagari}</p>
                <p className="text-sm opacity-75">{action.description}</p>
              </div>
            </Link>
          )
        })}
      </div>

      {/* Recent Activity */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Practice Summary */}
        <div className="carnatic-card p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Recent Practice</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
              <div>
                <h3 className="font-medium text-white">Sarali Varisai</h3>
                <p className="text-sm text-gray-400">Level 3 • Basic Patterns</p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-green-400">85%</div>
                <div className="text-xs text-gray-400">Accuracy</div>
              </div>
            </div>
            <div className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
              <div>
                <h3 className="font-medium text-white">Voice Calibration</h3>
                <p className="text-sm text-gray-400">Pitch Range Assessment</p>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-blue-400">92%</div>
                <div className="text-xs text-gray-400">Stability</div>
              </div>
            </div>
          </div>
        </div>

        {/* Learning Progress */}
        <div className="carnatic-card p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Learning Path</h2>
          <div className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                ✓
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-white">Sarali Varisai Foundations</h3>
                <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: '85%' }}></div>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-saffron-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                2
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-white">Janta Varisai</h3>
                <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                  <div className="bg-saffron-500 h-2 rounded-full" style={{ width: '45%' }}></div>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-white text-sm font-bold">
                3
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-400">Alankaram Patterns</h3>
                <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                  <div className="bg-gray-500 h-2 rounded-full" style={{ width: '10%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage