import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Home,
  BookOpen,
  Music,
  Target,
  TrendingUp,
  Users,
  Award,
  Settings,
  HelpCircle,
  X,
  ChevronRight
} from 'lucide-react'
import { cn } from '@/utils/cn'
import { Button } from '@/components/ui/Button'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
  isMobile: boolean
}

interface NavItem {
  name: string
  nameDevanagari: string
  href: string
  icon: React.ElementType
  badge?: string | number
  children?: NavItem[]
}

const navItems: NavItem[] = [
  {
    name: 'Dashboard',
    nameDevanagari: 'मुख्य पृष्ठ',
    href: '/',
    icon: Home
  },
  {
    name: 'Exercises',
    nameDevanagari: 'अभ्यास',
    href: '/exercises',
    icon: BookOpen,
    children: [
      {
        name: 'Sarali Varisai',
        nameDevanagari: 'सरली वरिसै',
        href: '/exercises/sarali',
        icon: Music
      },
      {
        name: 'Janta Varisai',
        nameDevanagari: 'जंता वरिसै',
        href: '/exercises/janta',
        icon: Music
      },
      {
        name: 'Alankaram',
        nameDevanagari: 'अलंकारम्',
        href: '/exercises/alankaram',
        icon: Music
      }
    ]
  },
  {
    name: 'Ragas',
    nameDevanagari: 'राग',
    href: '/ragas',
    icon: Music,
    badge: '72'
  },
  {
    name: 'Practice',
    nameDevanagari: 'अभ्यास',
    href: '/practice',
    icon: Target
  },
  {
    name: 'Progress',
    nameDevanagari: 'प्रगति',
    href: '/progress',
    icon: TrendingUp
  },
  {
    name: 'Community',
    nameDevanagari: 'समुदाय',
    href: '/community',
    icon: Users,
    badge: '5'
  },
  {
    name: 'Achievements',
    nameDevanagari: 'उपलब्धियाँ',
    href: '/achievements',
    icon: Award
  }
]

const bottomNavItems: NavItem[] = [
  {
    name: 'Settings',
    nameDevanagari: 'सेटिंग्स',
    href: '/settings',
    icon: Settings
  },
  {
    name: 'Help',
    nameDevanagari: 'सहायता',
    href: '/help',
    icon: HelpCircle
  }
]

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, isMobile }) => {
  const location = useLocation()
  const [expandedItems, setExpandedItems] = React.useState<string[]>([])

  const toggleExpanded = (href: string) => {
    setExpandedItems(prev =>
      prev.includes(href)
        ? prev.filter(item => item !== href)
        : [...prev, href]
    )
  }

  const isActiveLink = (href: string) => {
    return location.pathname === href || location.pathname.startsWith(href + '/')
  }

  const NavLink: React.FC<{ item: NavItem; level?: number }> = ({ item, level = 0 }) => {
    const active = isActiveLink(item.href)
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expandedItems.includes(item.href)

    return (
      <div>
        <Link
          to={hasChildren ? '#' : item.href}
          onClick={(e) => {
            if (hasChildren) {
              e.preventDefault()
              toggleExpanded(item.href)
            } else if (isMobile) {
              onClose()
            }
          }}
          className={cn(
            "flex items-center justify-between w-full px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 group",
            level > 0 && "ml-6",
            active
              ? "bg-gradient-to-r from-orange-500 to-red-500 text-white shadow-lg"
              : "text-gray-700 hover:bg-orange-50 hover:text-orange-700"
          )}
        >
          <div className="flex items-center space-x-3">
            <item.icon className={cn(
              "h-5 w-5 transition-colors",
              active ? "text-white" : "text-gray-500 group-hover:text-orange-500"
            )} />
            <div>
              <div className={cn(
                "font-medium",
                active ? "text-white" : "text-gray-900"
              )}>
                {item.name}
              </div>
              <div className={cn(
                "text-xs",
                active ? "text-orange-100" : "text-gray-500"
              )}>
                {item.nameDevanagari}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-1">
            {item.badge && (
              <span className={cn(
                "px-2 py-1 text-xs font-bold rounded-full",
                active
                  ? "bg-white/20 text-white"
                  : "bg-orange-100 text-orange-700"
              )}>
                {item.badge}
              </span>
            )}
            {hasChildren && (
              <motion.div
                animate={{ rotate: isExpanded ? 90 : 0 }}
                transition={{ duration: 0.2 }}
              >
                <ChevronRight className="h-4 w-4" />
              </motion.div>
            )}
          </div>
        </Link>

        {/* Children */}
        <AnimatePresence>
          {hasChildren && isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="mt-1 space-y-1">
                {item.children?.map((child) => (
                  <NavLink key={child.href} item={child} level={level + 1} />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white/95 backdrop-blur-sm border-r border-orange-100">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-orange-100">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center text-white shadow-lg">
            <Music className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-bold text-gray-900">संगीत शाला</h2>
            <p className="text-xs text-gray-500">Learning Hub</p>
          </div>
        </div>
        {isMobile && (
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}
      </nav>

      {/* Bottom Navigation */}
      <div className="p-4 border-t border-orange-100 space-y-1">
        {bottomNavItems.map((item) => (
          <NavLink key={item.href} item={item} />
        ))}
      </div>

      {/* User Progress Summary */}
      <div className="p-4 border-t border-orange-100">
        <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Today's Progress</span>
            <span className="text-xs text-orange-600">Level 5</span>
          </div>
          <div className="w-full bg-orange-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-orange-500 to-red-500 h-2 rounded-full" style={{width: '75%'}} />
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-600">
            <span>3 of 4 exercises</span>
            <span>12 day streak 🔥</span>
          </div>
        </div>
      </div>
    </div>
  )

  if (isMobile) {
    return (
      <AnimatePresence>
        {isOpen && (
          <motion.aside
            initial={{ x: -300 }}
            animate={{ x: 0 }}
            exit={{ x: -300 }}
            transition={{ type: 'tween', duration: 0.3 }}
            className="fixed left-0 top-16 bottom-0 w-64 z-40 shadow-xl"
          >
            {sidebarContent}
          </motion.aside>
        )}
      </AnimatePresence>
    )
  }

  return (
    <motion.aside
      initial={{ x: -300 }}
      animate={{ x: isOpen ? 0 : -300 }}
      transition={{ type: 'tween', duration: 0.3 }}
      className="fixed left-0 top-16 bottom-0 w-64 z-30 shadow-xl"
    >
      {sidebarContent}
    </motion.aside>
  )
}

export default Sidebar