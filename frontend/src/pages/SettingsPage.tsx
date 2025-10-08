import React from 'react'
import { useAuth } from '../contexts/AuthContext'

const SettingsPage: React.FC = () => {
  const { user, updateUser } = useAuth()

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-saffron-400 to-deepOrange-400 bg-clip-text text-transparent mb-4">
          सेटिंग्स • Settings
        </h1>
        <p className="text-xl text-gray-400">
          Customize your learning experience and manage your account preferences
        </p>
      </div>

      {/* Profile Settings */}
      <div className="carnatic-card p-6">
        <h2 className="text-2xl font-semibold text-saffron-400 mb-6">Profile Information</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Name
            </label>
            <input
              type="text"
              value={user?.name || ''}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-transparent"
              placeholder="Your full name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Email
            </label>
            <input
              type="email"
              value={user?.email || ''}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-transparent"
              placeholder="your.email@example.com"
            />
          </div>
        </div>
      </div>

      {/* Learning Preferences */}
      <div className="carnatic-card p-6">
        <h2 className="text-2xl font-semibold text-saffron-400 mb-6">Learning Preferences</h2>
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Musical Background
            </label>
            <select className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-transparent">
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Preferred Language
            </label>
            <select className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-transparent">
              <option value="en">English</option>
              <option value="hi">Hindi (हिन्दी)</option>
              <option value="ta">Tamil (தமிழ்)</option>
              <option value="te">Telugu (తెలుగు)</option>
              <option value="kn">Kannada (ಕನ್ನಡ)</option>
            </select>
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
            <div>
              <h3 className="text-white font-medium">Show Devanagari Script</h3>
              <p className="text-gray-400 text-sm">Display traditional script alongside English</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-saffron-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-saffron-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Audio Settings */}
      <div className="carnatic-card p-6">
        <h2 className="text-2xl font-semibold text-saffron-400 mb-6">Audio Settings</h2>
        <div className="space-y-6">
          <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
            <div>
              <h3 className="text-white font-medium">Auto Recording</h3>
              <p className="text-gray-400 text-sm">Automatically record practice sessions</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-saffron-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-saffron-600"></div>
            </label>
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
            <div>
              <h3 className="text-white font-medium">Real-time Feedback</h3>
              <p className="text-gray-400 text-sm">Show pitch accuracy during practice</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-saffron-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-saffron-600"></div>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Feedback Sensitivity
            </label>
            <select className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-transparent">
              <option value="low">Low - Less strict pitch accuracy</option>
              <option value="medium">Medium - Balanced feedback</option>
              <option value="high">High - Strict pitch accuracy</option>
            </select>
          </div>
        </div>
      </div>

      {/* Practice Settings */}
      <div className="carnatic-card p-6">
        <h2 className="text-2xl font-semibold text-saffron-400 mb-6">Practice Settings</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Daily Practice Goal (minutes)
            </label>
            <input
              type="number"
              min="5"
              max="120"
              defaultValue="30"
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Preferred Tempo (BPM)
            </label>
            <input
              type="number"
              min="60"
              max="200"
              defaultValue="120"
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-saffron-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between p-4 bg-slate-700/30 rounded-lg">
          <div>
            <h3 className="text-white font-medium">Practice Reminders</h3>
            <p className="text-gray-400 text-sm">Receive daily practice notifications</p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" className="sr-only peer" defaultChecked />
            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-saffron-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-saffron-600"></div>
          </label>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button className="cultural-button px-8 py-3 text-lg font-semibold">
          Save Settings
        </button>
      </div>
    </div>
  )
}

export default SettingsPage