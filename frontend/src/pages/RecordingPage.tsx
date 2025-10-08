import React from 'react'
import { RecordingInterface } from '../components/audio/RecordingInterface'
import { VoiceCalibration } from '../components/audio/VoiceCalibration'

const RecordingPage: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-saffron-400 to-deepOrange-400 bg-clip-text text-transparent mb-4">
          स्वर रिकॉर्डिंग • Voice Recording
        </h1>
        <p className="text-xl text-gray-400 max-w-3xl mx-auto">
          Professional-grade voice recording and analysis system for Carnatic music practice.
          Calibrate your voice, record sessions, and receive real-time feedback on your performance.
        </p>
      </div>

      {/* Voice Calibration Section */}
      <div className="carnatic-card p-6">
        <h2 className="text-2xl font-semibold text-saffron-400 mb-4">Voice Calibration</h2>
        <p className="text-gray-300 mb-6">
          Calibrate your voice range and characteristics for optimal pitch detection and feedback accuracy.
        </p>
        <VoiceCalibration />
      </div>

      {/* Recording Interface Section */}
      <div className="carnatic-card p-6">
        <h2 className="text-2xl font-semibold text-saffron-400 mb-4">Practice Recording</h2>
        <p className="text-gray-300 mb-6">
          Record your practice sessions with real-time pitch detection, visualization, and performance analysis.
        </p>
        <RecordingInterface />
      </div>

      {/* Recording Tips */}
      <div className="carnatic-card p-6">
        <h2 className="text-2xl font-semibold text-saffron-400 mb-4">Recording Best Practices</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-white mb-3">Environment Setup:</h3>
            <ul className="space-y-2 text-gray-300">
              <li>• Choose a quiet room with minimal echo</li>
              <li>• Position microphone 6-12 inches from your mouth</li>
              <li>• Maintain consistent distance during recording</li>
              <li>• Use headphones to monitor your recording</li>
              <li>• Ensure stable internet connection for analysis</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-white mb-3">Vocal Preparation:</h3>
            <ul className="space-y-2 text-gray-300">
              <li>• Warm up your voice before recording</li>
              <li>• Maintain proper posture while singing</li>
              <li>• Stay hydrated for optimal vocal performance</li>
              <li>• Practice breath control exercises</li>
              <li>• Record at your most comfortable vocal range</li>
            </ul>
          </div>
        </div>

        {/* Audio Quality Tips */}
        <div className="mt-6 bg-slate-700/30 rounded-lg p-4">
          <h4 className="font-medium text-white mb-3">Audio Quality Guidelines:</h4>
          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-medium text-green-400 mb-1">Sample Rate</div>
              <div className="text-gray-400">44.1 kHz or higher for professional quality</div>
            </div>
            <div>
              <div className="font-medium text-blue-400 mb-1">Bit Depth</div>
              <div className="text-gray-400">24-bit recommended for best dynamic range</div>
            </div>
            <div>
              <div className="font-medium text-orange-400 mb-1">Recording Level</div>
              <div className="text-gray-400">Aim for -12dB to -6dB peak levels</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RecordingPage