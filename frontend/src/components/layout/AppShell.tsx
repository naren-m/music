import React, { useState, useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Header from './Header'
import Sidebar from './Sidebar'
import Footer from './Footer'
import { cn } from '@/utils/cn'

interface AppShellProps {
  children?: React.ReactNode
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
      if (window.innerWidth >= 768) {
        setSidebarOpen(false)
      }
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen)
  }

  const closeSidebar = () => {
    setSidebarOpen(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-red-50 to-yellow-50">
      <Header onMenuToggle={handleSidebarToggle} />

      <div className="flex">
        {/* Sidebar */}
        <AnimatePresence>
          {(sidebarOpen && isMobile) && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
              onClick={closeSidebar}
            />
          )}
        </AnimatePresence>

        <Sidebar
          isOpen={sidebarOpen}
          onClose={closeSidebar}
          isMobile={isMobile}
        />

        {/* Main Content */}
        <main className={cn(
          "flex-1 transition-all duration-300 ease-in-out",
          "min-h-screen pt-16", // Account for fixed header
          sidebarOpen && !isMobile ? "ml-64" : "ml-0"
        )}>
          <div className="container mx-auto px-4 py-6 max-w-7xl">
            {children || <Outlet />}
          </div>
        </main>
      </div>

      <Footer />
    </div>
  )
}

