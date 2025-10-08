import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Eye, EyeOff, Music, Mail, Lock, User, Loader2, AlertCircle,
  CheckCircle, Calendar, MapPin
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'

interface SignupFormProps {
  onSignup?: (userData: SignupData) => Promise<void>
  className?: string
}

interface SignupData {
  firstName: string
  lastName: string
  email: string
  password: string
  age?: number
  location?: string
  musicalBackground: 'beginner' | 'intermediate' | 'advanced'
  instruments: string[]
  learningGoals: string[]
  newsletter: boolean
}

const SignupForm: React.FC<SignupFormProps> = ({ onSignup, className }) => {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState<SignupData>({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    age: undefined,
    location: '',
    musicalBackground: 'beginner',
    instruments: [],
    learningGoals: [],
    newsletter: true
  })

  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [passwordStrength, setPasswordStrength] = useState(0)

  const instruments = [
    'Voice', 'Violin', 'Veena', 'Flute', 'Mridangam', 'Tabla',
    'Ghatam', 'Kanjira', 'Harmonium', 'Other'
  ]

  const learningGoals = [
    'Classical Performance', 'Spiritual Growth', 'Cultural Connection',
    'Professional Development', 'Personal Enjoyment', 'Teaching Others'
  ]

  const calculatePasswordStrength = (password: string) => {
    let strength = 0
    if (password.length >= 8) strength++
    if (/[A-Z]/.test(password)) strength++
    if (/[a-z]/.test(password)) strength++
    if (/[0-9]/.test(password)) strength++
    if (/[^A-Za-z0-9]/.test(password)) strength++
    return strength
  }

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (error) setError(null)

    if (field === 'password') {
      setPasswordStrength(calculatePasswordStrength(value))
    }
  }

  const handleArrayToggle = (field: 'instruments' | 'learningGoals', value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field].includes(value)
        ? prev[field].filter(item => item !== value)
        : [...prev[field], value]
    }))
  }

  const validateStep = (step: number) => {
    switch (step) {
      case 1:
        return formData.firstName && formData.lastName && formData.email && formData.password.length >= 8
      case 2:
        return formData.musicalBackground
      case 3:
        return true // Optional step
      default:
        return true
    }
  }

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, 3))
    }
  }

  const handlePrev = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      if (onSignup) {
        await onSignup(formData)
      } else {
        // Mock signup
        await new Promise(resolve => setTimeout(resolve, 2000))
        navigate('/welcome') // Navigate to welcome page
      }
    } catch (err: any) {
      setError(err.message || 'Signup failed. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const getPasswordStrengthColor = () => {
    switch (passwordStrength) {
      case 0: case 1: return 'bg-red-500'
      case 2: case 3: return 'bg-yellow-500'
      case 4: case 5: return 'bg-green-500'
      default: return 'bg-gray-300'
    }
  }

  const getPasswordStrengthText = () => {
    switch (passwordStrength) {
      case 0: case 1: return 'Weak'
      case 2: case 3: return 'Moderate'
      case 4: case 5: return 'Strong'
      default: return ''
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={cn("w-full max-w-lg mx-auto", className)}
    >
      {/* Header */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring" }}
          className="w-16 h-16 bg-gradient-to-br from-orange-500 to-red-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg"
        >
          <Music className="h-8 w-8 text-white" />
        </motion.div>

        <h1 className="text-3xl font-bold text-gray-900">Join Our Community</h1>
        <h2 className="text-xl text-orange-600 font-medium">हमारे समुदाय में शामिल हों</h2>
        <p className="text-gray-600 mt-2">
          Begin your journey into Carnatic music
        </p>
      </div>

      {/* Progress Indicator */}
      <div className="flex justify-center mb-8">
        {[1, 2, 3].map((step) => (
          <div key={step} className="flex items-center">
            <div className={cn(
              "w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all",
              currentStep >= step
                ? "bg-gradient-to-r from-orange-500 to-red-500 text-white"
                : "bg-gray-200 text-gray-500"
            )}>
              {currentStep > step ? <CheckCircle className="h-5 w-5" /> : step}
            </div>
            {step < 3 && (
              <div className={cn(
                "w-16 h-0.5 mx-2 transition-colors",
                currentStep > step ? "bg-orange-500" : "bg-gray-300"
              )} />
            )}
          </div>
        ))}
      </div>

      {/* Step Labels */}
      <div className="flex justify-between text-xs text-gray-500 mb-8 px-4">
        <span className={currentStep >= 1 ? "text-orange-600" : ""}>Account</span>
        <span className={currentStep >= 2 ? "text-orange-600" : ""}>Background</span>
        <span className={currentStep >= 3 ? "text-orange-600" : ""}>Preferences</span>
      </div>

      {/* Error Alert */}
      {error && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 mb-6"
        >
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span className="text-sm">{error}</span>
        </motion.div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit}>
        {/* Step 1: Account Details */}
        {currentStep === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {/* Name Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 block">
                  First Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                  <input
                    type="text"
                    value={formData.firstName}
                    onChange={(e) => handleInputChange('firstName', e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white"
                    placeholder="First name"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 block">
                  Last Name
                </label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white"
                  placeholder="Last name"
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 block">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white"
                  placeholder="Enter your email address"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700 block">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => handleInputChange('password', e.target.value)}
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white"
                  placeholder="Create a strong password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>

              {/* Password Strength Indicator */}
              {formData.password && (
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className={cn("h-2 rounded-full transition-all", getPasswordStrengthColor())}
                        style={{width: `${(passwordStrength / 5) * 100}%`}}
                      />
                    </div>
                    <span className="text-xs text-gray-600">{getPasswordStrengthText()}</span>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Step 2: Musical Background */}
        {currentStep === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {/* Age and Location */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 block">
                  Age (Optional)
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                  <input
                    type="number"
                    value={formData.age || ''}
                    onChange={(e) => handleInputChange('age', parseInt(e.target.value) || undefined)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white"
                    placeholder="Age"
                    min="5"
                    max="120"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 block">
                  Location (Optional)
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200 bg-gray-50 focus:bg-white"
                    placeholder="City, Country"
                  />
                </div>
              </div>
            </div>

            {/* Musical Background */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700 block">
                Musical Background
                <span className="text-gray-500 ml-1">संगीत पृष्ठभूमि</span>
              </label>
              <div className="grid grid-cols-1 gap-3">
                {[
                  { value: 'beginner', label: 'Beginner', desc: 'New to Carnatic music' },
                  { value: 'intermediate', label: 'Intermediate', desc: 'Some experience with basics' },
                  { value: 'advanced', label: 'Advanced', desc: 'Experienced practitioner' }
                ].map((option) => (
                  <label key={option.value} className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-orange-50 transition-colors">
                    <input
                      type="radio"
                      name="musicalBackground"
                      value={option.value}
                      checked={formData.musicalBackground === option.value}
                      onChange={(e) => handleInputChange('musicalBackground', e.target.value as any)}
                      className="text-orange-500 border-gray-300 focus:ring-orange-500"
                    />
                    <div>
                      <div className="font-medium text-gray-900">{option.label}</div>
                      <div className="text-sm text-gray-500">{option.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </motion.div>
        )}

        {/* Step 3: Preferences */}
        {currentStep === 3 && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            {/* Instruments */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700 block">
                Instruments of Interest (Optional)
              </label>
              <div className="grid grid-cols-2 gap-2">
                {instruments.map((instrument) => (
                  <label key={instrument} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.instruments.includes(instrument)}
                      onChange={() => handleArrayToggle('instruments', instrument)}
                      className="text-orange-500 border-gray-300 rounded focus:ring-orange-500"
                    />
                    <span className="text-sm text-gray-700">{instrument}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Learning Goals */}
            <div className="space-y-3">
              <label className="text-sm font-medium text-gray-700 block">
                Learning Goals (Optional)
              </label>
              <div className="grid grid-cols-1 gap-2">
                {learningGoals.map((goal) => (
                  <label key={goal} className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={formData.learningGoals.includes(goal)}
                      onChange={() => handleArrayToggle('learningGoals', goal)}
                      className="text-orange-500 border-gray-300 rounded focus:ring-orange-500"
                    />
                    <span className="text-sm text-gray-700">{goal}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Newsletter */}
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.newsletter}
                onChange={(e) => handleInputChange('newsletter', e.target.checked)}
                className="text-orange-500 border-gray-300 rounded focus:ring-orange-500"
              />
              <label className="text-sm text-gray-700">
                Send me updates about new features and learning content
              </label>
            </div>
          </motion.div>
        )}

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8">
          {currentStep > 1 ? (
            <Button
              type="button"
              variant="outline"
              onClick={handlePrev}
            >
              Previous
            </Button>
          ) : <div />}

          {currentStep < 3 ? (
            <Button
              type="button"
              variant="carnatic"
              onClick={handleNext}
              disabled={!validateStep(currentStep)}
            >
              Next
            </Button>
          ) : (
            <Button
              type="submit"
              variant="carnatic"
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Creating Account...</span>
                </div>
              ) : (
                'Create Account'
              )}
            </Button>
          )}
        </div>
      </form>

      {/* Sign In Link */}
      <div className="mt-8 text-center">
        <p className="text-gray-600">
          Already have an account?{' '}
          <Link
            to="/login"
            className="text-orange-600 hover:text-orange-700 font-medium"
          >
            Sign in
          </Link>
        </p>
      </div>
    </motion.div>
  )
}

export { SignupForm }