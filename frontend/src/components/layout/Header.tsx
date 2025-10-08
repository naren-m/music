import React from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Menu, Search, Bell, Settings, User, LogOut, Music } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'
import UserMenu from './UserMenu'

interface HeaderProps {
  onMenuToggle: () => void
}

const Header: React.FC<HeaderProps> = ({ onMenuToggle }) => {
  const navigate = useNavigate()
  const [user, setUser] = React.useState<any>(null) // Will be replaced with auth context
  const [showUserMenu, setShowUserMenu] = React.useState(false)

  // Mock user for now - will be replaced with actual auth
  React.useEffect(() => {
    // Mock authentication check
    const mockUser = {
      name: "राज Kumar",
      email: "raj@example.com",
      avatar: null,
      subscription: "premium",
      progress: {
        level: 5,
        streak: 12
      }
    }
    setUser(mockUser)
  }, [])

  const handleSearch = (query: string) => {
    // Implement search functionality
    console.log('Search:', query)
  }

  const handleNotifications = () => {
    navigate('/notifications')
  }

  const handleSettings = () => {
    navigate('/settings')
  }

  const handleLogout = () => {
    // Implement logout
    setUser(null)
    navigate('/login')
  }

  return (
    <motion.header
      initial={{ y: -64 }}
      animate={{ y: 0 }}
      className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-orange-100 shadow-sm"
    >
      <div className="flex items-center justify-between h-16 px-4 mx-auto max-w-7xl">
        {/* Left: Menu + Logo */}
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuToggle}
            className="md:hidden"
          >
            <Menu className="h-5 w-5" />
          </Button>

          <Link
            to="/"
            className="flex items-center space-x-2 group"
          >
            <div className="relative">
              <motion.div
                whileHover={{ rotate: 10, scale: 1.1 }}
                className="w-8 h-8 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center text-white shadow-lg"
              >
                <Music className="h-5 w-5" />
              </motion.div>
            </div>
            <div className="hidden sm:block">
              <h1 className="text-xl font-bold bg-gradient-to-r from-orange-600 to-red-600 bg-clip-text text-transparent">
                संगीत शाला
              </h1>
              <p className="text-xs text-gray-500 -mt-1">Carnatic Learning</p>
            </div>
          </Link>
        </div>

        {/* Center: Search (Desktop) */}
        <div className="hidden md:flex flex-1 max-w-md mx-8">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search exercises, ragas, compositions..."
              className="w-full pl-10 pr-4 py-2 text-sm bg-gray-50 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              onChange={(e) => handleSearch(e.target.value)}
            />
          </div>
        </div>

        {/* Right: User Actions */}
        <div className="flex items-center space-x-2">
          {/* Search (Mobile) */}
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
          >
            <Search className="h-5 w-5" />
          </Button>

          {user ? (
            <>
              {/* Notifications */}
              <Button
                variant="ghost"
                size="icon"
                onClick={handleNotifications}
                className="relative"
              >
                <Bell className="h-5 w-5" />
                <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full flex items-center justify-center">
                  <span className="text-xs text-white font-bold">2</span>
                </span>
              </Button>

              {/* Settings */}
              <Button
                variant="ghost"
                size="icon"
                onClick={handleSettings}
              >
                <Settings className="h-5 w-5" />
              </Button>

              {/* User Menu */}
              <div className="relative">
                <Button
                  variant="ghost"
                  className="flex items-center space-x-2 px-3 py-2"
                  onClick={() => setShowUserMenu(!showUserMenu)}
                >
                  {user.avatar ? (
                    <img
                      src={user.avatar}
                      alt={user.name}
                      className="w-6 h-6 rounded-full"
                    />
                  ) : (
                    <div className="w-6 h-6 bg-gradient-to-br from-orange-400 to-red-400 rounded-full flex items-center justify-center text-white text-xs font-bold">
                      {user.name.charAt(0)}
                    </div>
                  )}
                  <span className="hidden sm:block text-sm font-medium">
                    {user.name}
                  </span>
                </Button>

                <UserMenu
                  user={user}
                  isOpen={showUserMenu}
                  onClose={() => setShowUserMenu(false)}
                  onLogout={handleLogout}
                />
              </div>
            </>
          ) : (
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/login')}
              >
                Login
              </Button>
              <Button
                variant="carnatic"
                size="sm"
                onClick={() => navigate('/signup')}
              >
                Sign Up
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Progress Bar (if user is logged in) */}
      {user && (
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          className="h-1 bg-gradient-to-r from-orange-500 to-red-500"
          style={{
            transformOrigin: 'left',
            width: `${(user.progress.level / 10) * 100}%`
          }}
        />
      )}
    </motion.header>
  )
}

export default Header