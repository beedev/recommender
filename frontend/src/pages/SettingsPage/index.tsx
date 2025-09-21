import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { User, Bell, Shield, Palette, Globe, Save } from 'lucide-react'
import Button from '@components/common/Button'
import { useAppSelector, useAppDispatch } from '@hooks/redux'
import { setTheme, setLanguage } from '@store/slices/uiSlice'
import { SUPPORTED_LANGUAGES, changeLanguage } from '@locales/i18n'

const SettingsPage: React.FC = () => {
  const { t } = useTranslation(['auth', 'common'])
  const dispatch = useAppDispatch()
  const { theme, language } = useAppSelector(state => state.ui)
  const [activeTab, setActiveTab] = useState('profile')

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'appearance', label: 'Appearance', icon: Palette },
    { id: 'language', label: 'Language', icon: Globe },
  ]

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    dispatch(setTheme(newTheme))
  }

  const handleLanguageChange = async (newLanguage: string) => {
    dispatch(setLanguage(newLanguage))
    await changeLanguage(newLanguage as any)
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-white">{t('auth:profile.personal_info')}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-white text-opacity-80 mb-2">
                  {t('common:first_name')}
                </label>
                <input
                  type="text"
                  className="w-full px-4 py-2 bg-white bg-opacity-10 text-white rounded-lg border border-white border-opacity-20 focus:outline-none focus:ring-2 focus:ring-sparky-gold focus:border-transparent"
                  placeholder="John"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white text-opacity-80 mb-2">
                  {t('common:last_name')}
                </label>
                <input
                  type="text"
                  className="w-full px-4 py-2 bg-white bg-opacity-10 text-white rounded-lg border border-white border-opacity-20 focus:outline-none focus:ring-2 focus:ring-sparky-gold focus:border-transparent"
                  placeholder="Doe"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-white text-opacity-80 mb-2">
                  {t('common:email')}
                </label>
                <input
                  type="email"
                  className="w-full px-4 py-2 bg-white bg-opacity-10 text-white rounded-lg border border-white border-opacity-20 focus:outline-none focus:ring-2 focus:ring-sparky-gold focus:border-transparent"
                  placeholder="john.doe@esab.com"
                />
              </div>
            </div>
          </div>
        )

      case 'notifications':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-white">Notification Preferences</h2>
            <div className="space-y-4">
              {[
                { id: 'email', label: 'Email notifications', description: 'Receive notifications via email' },
                { id: 'push', label: 'Push notifications', description: 'Receive push notifications in browser' },
                { id: 'sparky', label: 'Sparky updates', description: 'Get notified about Sparky AI improvements' },
                { id: 'inventory', label: 'Inventory alerts', description: 'Low stock and inventory updates' },
              ].map((notification) => (
                <div key={notification.id} className="flex items-center justify-between p-4 bg-white bg-opacity-5 rounded-lg">
                  <div>
                    <h3 className="text-white font-medium">{notification.label}</h3>
                    <p className="text-white text-opacity-60 text-sm">{notification.description}</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" className="sr-only peer" defaultChecked />
                    <div className="relative w-11 h-6 bg-white bg-opacity-20 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-sparky-gold peer-focus:ring-opacity-20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-sparky-gold"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>
        )

      case 'security':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-white">{t('auth:profile.security')}</h2>
            <div className="space-y-4">
              <div className="p-4 bg-white bg-opacity-5 rounded-lg">
                <h3 className="text-white font-medium mb-2">{t('auth:profile.change_password')}</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-white text-opacity-80 mb-2">
                      {t('auth:profile.current_password')}
                    </label>
                    <input
                      type="password"
                      className="w-full px-4 py-2 bg-white bg-opacity-10 text-white rounded-lg border border-white border-opacity-20 focus:outline-none focus:ring-2 focus:ring-sparky-gold focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white text-opacity-80 mb-2">
                      {t('auth:profile.new_password')}
                    </label>
                    <input
                      type="password"
                      className="w-full px-4 py-2 bg-white bg-opacity-10 text-white rounded-lg border border-white border-opacity-20 focus:outline-none focus:ring-2 focus:ring-sparky-gold focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-white text-opacity-80 mb-2">
                      {t('auth:profile.confirm_new_password')}
                    </label>
                    <input
                      type="password"
                      className="w-full px-4 py-2 bg-white bg-opacity-10 text-white rounded-lg border border-white border-opacity-20 focus:outline-none focus:ring-2 focus:ring-sparky-gold focus:border-transparent"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )

      case 'appearance':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-white">Appearance</h2>
            <div className="space-y-4">
              <div className="p-4 bg-white bg-opacity-5 rounded-lg">
                <h3 className="text-white font-medium mb-4">{t('common:theme')}</h3>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { key: 'light', label: t('common:light'), icon: '☀️' },
                    { key: 'dark', label: t('common:dark'), icon: '🌙' },
                    { key: 'system', label: t('common:system'), icon: '💻' },
                  ].map((themeOption) => (
                    <button
                      key={themeOption.key}
                      onClick={() => handleThemeChange(themeOption.key as any)}
                      className={`p-4 rounded-lg border-2 transition-colors ${
                        theme === themeOption.key
                          ? 'border-sparky-gold bg-sparky-gold bg-opacity-10'
                          : 'border-white border-opacity-20 hover:border-opacity-40'
                      }`}
                    >
                      <div className="text-2xl mb-2">{themeOption.icon}</div>
                      <div className="text-white text-sm">{themeOption.label}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )

      case 'language':
        return (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-white">{t('common:language')}</h2>
            <div className="space-y-4">
              <div className="p-4 bg-white bg-opacity-5 rounded-lg">
                <h3 className="text-white font-medium mb-4">Select Language</h3>
                <div className="space-y-2">
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      onClick={() => handleLanguageChange(lang.code)}
                      className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                        language === lang.code
                          ? 'bg-sparky-gold bg-opacity-20 border border-sparky-gold'
                          : 'bg-white bg-opacity-5 border border-white border-opacity-20 hover:bg-opacity-10'
                      }`}
                    >
                      <span className="text-xl">{lang.flag}</span>
                      <div className="flex-1 text-left">
                        <div className="text-white font-medium">{lang.name}</div>
                        <div className="text-white text-opacity-60 text-sm">{lang.nativeName}</div>
                      </div>
                      {language === lang.code && (
                        <div className="w-2 h-2 bg-sparky-gold rounded-full"></div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">{t('common:settings')}</h1>
          <p className="text-white text-opacity-70 mt-1">Manage your account preferences and settings</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <nav className="space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-left transition-colors ${
                      activeTab === tab.id
                        ? 'bg-sparky-gold bg-opacity-20 text-sparky-gold border border-sparky-gold'
                        : 'text-white hover:bg-white hover:bg-opacity-5'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {tab.label}
                  </button>
                )
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 border border-white border-opacity-20">
              {renderTabContent()}
              
              {/* Save Button */}
              <div className="mt-8 pt-6 border-t border-white border-opacity-20">
                <Button 
                  variant="primary" 
                  leftIcon={<Save className="w-4 h-4" />}
                >
                  {t('common:save')} Changes
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage