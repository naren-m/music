import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'

// Context Providers
import { AuthProvider } from './contexts/AuthContext'
import { AudioProvider } from './contexts/AudioContext'
import { PracticeSessionProvider } from './contexts/PracticeSessionContext'

// Layout Components
import { AppShell } from './components/layout/AppShell'

// Page Components
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'
import DashboardPage from './pages/DashboardPage'
import ExercisesPage from './pages/ExercisesPage'
import SaraliExercisePage from './pages/exercises/SaraliExercisePage'
import JantaExercisePage from './pages/exercises/JantaExercisePage'
import AlankaramExercisePage from './pages/exercises/AlankaramExercisePage'
import RecordingPage from './pages/RecordingPage'
import SettingsPage from './pages/SettingsPage'

// Protected Route Component
import ProtectedRoute from './components/auth/ProtectedRoute'

const App: React.FC = () => {
  return (
    <Router>
      <AuthProvider>
        <AudioProvider>
          <PracticeSessionProvider>
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
              <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/signup" element={<SignupPage />} />

                {/* Protected Routes */}
                <Route path="/" element={
                  <ProtectedRoute>
                    <AppShell>
                      <Navigate to="/dashboard" replace />
                    </AppShell>
                  </ProtectedRoute>
                } />

                <Route path="/dashboard" element={
                  <ProtectedRoute>
                    <AppShell>
                      <DashboardPage />
                    </AppShell>
                  </ProtectedRoute>
                } />

                <Route path="/exercises" element={
                  <ProtectedRoute>
                    <AppShell>
                      <ExercisesPage />
                    </AppShell>
                  </ProtectedRoute>
                } />

                <Route path="/exercises/sarali" element={
                  <ProtectedRoute>
                    <AppShell>
                      <SaraliExercisePage />
                    </AppShell>
                  </ProtectedRoute>
                } />

                <Route path="/exercises/janta" element={
                  <ProtectedRoute>
                    <AppShell>
                      <JantaExercisePage />
                    </AppShell>
                  </ProtectedRoute>
                } />

                <Route path="/exercises/alankaram" element={
                  <ProtectedRoute>
                    <AppShell>
                      <AlankaramExercisePage />
                    </AppShell>
                  </ProtectedRoute>
                } />

                <Route path="/recording" element={
                  <ProtectedRoute>
                    <AppShell>
                      <RecordingPage />
                    </AppShell>
                  </ProtectedRoute>
                } />

                <Route path="/settings" element={
                  <ProtectedRoute>
                    <AppShell>
                      <SettingsPage />
                    </AppShell>
                  </ProtectedRoute>
                } />

                {/* Catch-all redirect */}
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </div>
          </PracticeSessionProvider>
        </AudioProvider>
      </AuthProvider>
    </Router>
  )
}

export default App