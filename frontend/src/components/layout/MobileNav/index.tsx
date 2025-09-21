import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Menu,
  X,
  Zap,
  Gauge,
  FileText,
} from 'lucide-react'
import clsx from 'clsx'
import { Badge } from '@components/common'

const navigation = [
  {
    name: 'sparky',
    href: '/sparky',
    icon: Zap,
    label: 'Sparky - Product Config',
  },
  {
    name: 'dashboard',
    href: '/dashboard',
    icon: Gauge,
    label: 'System Dashboard',
  },
  {
    name: 'quotes',
    href: '/quotes',
    icon: FileText,
    label: 'Quote Management',
  },
]

const MobileNav: React.FC = () => {
  const { t } = useTranslation('navigation')
  const location = useLocation()
  const [isOpen, setIsOpen] = useState(false)

  const toggleNav = () => setIsOpen(!isOpen)
  const closeNav = () => setIsOpen(false)

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={toggleNav}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-black bg-opacity-80 text-primary-400 rounded-md backdrop-blur-sm"
        aria-label="Toggle navigation"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Mobile Navigation Overlay */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="lg:hidden fixed inset-0 z-40 bg-black bg-opacity-50"
              onClick={closeNav}
            />

            {/* Mobile Sidebar */}
            <motion.div
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'tween', duration: 0.3 }}
              className="lg:hidden fixed inset-y-0 left-0 z-50 w-80 bg-black bg-opacity-90 border-r-2 border-primary-500 backdrop-blur-sm"
            >
              {/* Header */}
              <div className="p-6 pt-16">
                <h2 className="text-white text-xl font-bold mb-6">
                  {t('navigation', { defaultValue: 'Navigation' })}
                </h2>
              </div>
              
              {/* Navigation */}
              <nav>
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href || 
                    (item.href !== '/' && location.pathname.startsWith(item.href))
                  
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={closeNav}
                      className={clsx(
                        'flex items-center gap-3 px-6 py-4 text-white cursor-pointer transition-all duration-300 border-l-4',
                        isActive
                          ? 'bg-primary-500 bg-opacity-20 border-primary-500 font-bold'
                          : 'border-transparent hover:bg-primary-500 hover:bg-opacity-10 hover:border-primary-500'
                      )}
                    >
                      <item.icon className="h-5 w-5 flex-shrink-0" />
                      <span>{item.label}</span>
                    </Link>
                  )
                })}
              </nav>
              
              {/* Footer - System Status */}
              <div className="absolute bottom-0 left-0 right-0 p-6">
                <div className="text-xs text-neutral-400">
                  <p className="mb-2">{t('system_status', { defaultValue: 'System Status' })}</p>
                  <div className="flex items-center gap-2">
                    <Badge 
                      variant="success" 
                      size="sm" 
                      dot
                      className="text-success-400 bg-transparent"
                    >
                      {t('all_systems_online', { defaultValue: 'All Systems Online' })}
                    </Badge>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}

export default MobileNav