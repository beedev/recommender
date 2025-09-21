import React from 'react'
import { useTranslation } from 'react-i18next'
import { Power } from 'lucide-react'
import { Avatar } from '@components/common'

const Header: React.FC = () => {
  const { t } = useTranslation(['navigation', 'common'])

  return (
    <header className="bg-primary-400 p-4 shadow-lg">
      <div className="flex items-center justify-between max-w-full mx-auto">
        {/* ESAB Logo */}
        <div className="flex items-center gap-6">
          <div className="bg-black px-6 py-2 transform -skew-x-12">
            <span className="font-black text-primary-400 text-xl transform skew-x-12 inline-block">
              ESAB
            </span>
          </div>
          <h1 className="text-black font-bold text-xl">
            {t('system_title', { defaultValue: 'Welding Management System' })}
          </h1>
        </div>
        
        {/* User Profile */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-black text-sm">
              {t('welcome', { defaultValue: 'Welcome' })}
            </div>
            <div className="text-black font-bold">
              Jane Chapman
            </div>
          </div>
          <Avatar
            fallback="Jane Chapman"
            size="lg"
            className="bg-black text-primary-400"
          />
          <button 
            className="text-black hover:text-neutral-700 transition-colors p-2 rounded-md hover:bg-black hover:bg-opacity-10"
            aria-label={t('logout', { defaultValue: 'Logout' })}
          >
            <Power className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header