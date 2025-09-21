import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
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

const Sidebar: React.FC = () => {
  const { t } = useTranslation('navigation')
  const location = useLocation()

  return (
    <div className="sidebar bg-black bg-opacity-80 border-r-2 border-primary-500 backdrop-blur-sm">
      {/* Header */}
      <div className="p-6">
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
              className={clsx(
                'sidebar-item flex items-center gap-3 px-5 py-4 text-white cursor-pointer transition-all duration-300 border-l-4',
                isActive
                  ? 'active bg-primary-500 bg-opacity-20 border-primary-500 font-bold'
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
      <div className="p-6 mt-auto">
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
    </div>
  )
}

export default Sidebar