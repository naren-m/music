import React from 'react'
import { SignupForm } from '../components/auth/SignupForm'

const SignupPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-saffron-400 to-deepOrange-400 bg-clip-text text-transparent mb-2">
            संगीत शाला
          </h1>
          <p className="text-gray-400">Begin your Carnatic music learning journey</p>
        </div>
        <SignupForm />
      </div>
    </div>
  )
}

export default SignupPage