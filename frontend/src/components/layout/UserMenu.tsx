import React from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  User,
  Settings,
  Award,
  BarChart3,
  Bell,
  HelpCircle,
  LogOut,
  Crown
} from 'lucide-react'
import { cn } from '@/utils/cn'

interface UserMenuProps {
  user: {
    name: string
    email: string
    avatar?: string
    subscription: 'free' | 'premium' | 'master'
    progress: {
      level: number
      streak: number
    }
  }
  isOpen: boolean
  onClose: () => void
  onLogout: () => void
}

const UserMenu: React.FC<UserMenuProps> = ({ user, isOpen, onClose, onLogout }) => {
  const getSubscriptionBadge = () => {
    switch (user.subscription) {
      case 'premium':
        return { text: 'Premium', color: 'text-yellow-600 bg-yellow-100', icon: Crown }
      case 'master':
        return { text: 'Master', color: 'text-purple-600 bg-purple-100', icon: Crown }
      default:
        return { text: 'Free', color: 'text-gray-600 bg-gray-100', icon: null }
    }
  }

  const badge = getSubscriptionBadge()
  const BadgeIcon = badge.icon

  const menuItems = [
    {
      name: 'Profile',
      nameDevanagari: 'प्रोफाइल',
      href: '/profile',
      icon: User
    },
    {
      name: 'Progress',
      nameDevanagari: 'प्रगति',
      href: '/progress',
      icon: BarChart3
    },
    {
      name: 'Achievements',
      nameDevanagari: 'उपलब्धियाँ',
      href: '/achievements',
      icon: Award
    },
    {
      name: 'Settings',
      nameDevanagari: 'सेटिंग्स',
      href: '/settings',
      icon: Settings
    },
    {
      name: 'Notifications',
      nameDevanagari: 'सूचनाएं',
      href: '/notifications',
      icon: Bell
    },
    {
      name: 'Help & Support',
      nameDevanagari: 'सहायता',
      href: '/help',
      icon: HelpCircle
    }
  ]

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={onClose}
          />

          {/* Menu */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 top-full mt-2 w-80 bg-white rounded-lg shadow-xl border border-orange-100 z-50 overflow-hidden"
          >
            {/* User Info Header */}
            <div className="p-4 bg-gradient-to-r from-orange-50 to-red-50 border-b border-orange-100">
              <div className="flex items-center space-x-3">
                {user.avatar ? (
                  <img
                    src={user.avatar}
                    alt={user.name}
                    className="w-12 h-12 rounded-full"
                  />
                ) : (
                  <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-red-400 rounded-full flex items-center justify-center text-white text-lg font-bold">
                    {user.name.charAt(0)}
                  </div>
                )}
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="font-semibold text-gray-900">{user.name}</h3>
                    <span className={cn(
                      "inline-flex items-center px-2 py-1 rounded-full text-xs font-medium",
                      badge.color
                    )}>
                      {BadgeIcon && <BadgeIcon className="h-3 w-3 mr-1" />}
                      {badge.text}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{user.email}</p>
                  <div className="flex items-center space-x-3 mt-2 text-xs text-gray-500">
                    <span>Level {user.progress.level}</span>
                    <span>•</span>
                    <span>{user.progress.streak} day streak 🔥</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="px-4 py-3 bg-gray-50 border-b">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-gray-700">Weekly Goal</span>
                <span className="text-sm text-orange-600">5 of 7 days</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-orange-500 to-red-500 h-2 rounded-full transition-all duration-300"
                  style={{width: `${(5/7) * 100}%`}}
                />
              </div>
            </div>

            {/* Menu Items */}
            <div className="py-2">
              {menuItems.map((item, index) => (
                <Link
                  key={item.href}
                  to={item.href}
                  onClick={onClose}
                  className="flex items-center space-x-3 px-4 py-2 text-sm text-gray-700 hover:bg-orange-50 hover:text-orange-700 transition-colors"
                >
                  <item.icon className="h-4 w-4" />
                  <div>
                    <div className="font-medium">{item.name}</div>
                    <div className="text-xs text-gray-500">{item.nameDevanagari}</div>
                  </div>
                </Link>
              ))}
            </div>

            {/* Logout */}
            <div className="border-t border-gray-100">
              <button
                onClick={() => {
                  onLogout()
                  onClose()
                }}
                className="w-full flex items-center space-x-3 px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                <div>
                  <div className="font-medium">Sign out</div>
                  <div className="text-xs text-gray-500">साइन आउट</div>
                </div>
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default UserMenu