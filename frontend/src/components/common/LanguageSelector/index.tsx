import React from 'react'
import { useTranslation } from 'react-i18next'
import { SUPPORTED_LANGUAGES, changeLanguage, type SupportedLanguage } from '../../../locales/i18n'

interface LanguageSelectorProps {
  className?: string
  variant?: 'dropdown' | 'buttons'
  showFlags?: boolean
  showNativeNames?: boolean
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  className = '',
  variant = 'dropdown',
  showFlags = true,
  showNativeNames = true
}) => {
  const { i18n, t } = useTranslation('common')
  const currentLanguage = i18n.language as SupportedLanguage

  const handleLanguageChange = async (languageCode: SupportedLanguage) => {
    try {
      await changeLanguage(languageCode)
      // Notify parent components or services about language change
      window.dispatchEvent(new CustomEvent('languageChanged', { 
        detail: { language: languageCode } 
      }))
    } catch (error) {
      console.error('Failed to change language:', error)
    }
  }

  if (variant === 'buttons') {
    return (
      <div className={`flex gap-2 ${className}`}>
        {SUPPORTED_LANGUAGES.map((lang) => (
          <button
            key={lang.code}
            onClick={() => handleLanguageChange(lang.code)}
            className={`
              px-3 py-2 rounded-md text-sm font-medium transition-colors
              ${currentLanguage === lang.code
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
            title={lang.name}
          >
            {showFlags && <span className="mr-1">{lang.flag}</span>}
            {showNativeNames ? lang.nativeName : lang.code.toUpperCase()}
          </button>
        ))}
      </div>
    )
  }

  return (
    <div className={`relative ${className}`}>
      <select
        value={currentLanguage}
        onChange={(e) => handleLanguageChange(e.target.value as SupportedLanguage)}
        className="
          appearance-none bg-white border border-gray-300 rounded-md px-3 py-2 pr-8
          text-sm font-medium text-gray-700 hover:border-gray-400 focus:outline-none
          focus:ring-2 focus:ring-blue-500 focus:border-blue-500
        "
        title={t('language')}
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {showFlags ? `${lang.flag} ` : ''}
            {showNativeNames ? lang.nativeName : lang.name}
          </option>
        ))}
      </select>
      
      {/* Dropdown arrow */}
      <div className="absolute inset-y-0 right-0 flex items-center px-2 pointer-events-none">
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  )
}

export default LanguageSelector