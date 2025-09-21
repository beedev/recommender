import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  SUPPORTED_LANGUAGES, 
  changeLanguage, 
  getLanguageInfo, 
  type SupportedLanguage 
} from '../locales/i18n'

interface UseLanguageReturn {
  currentLanguage: SupportedLanguage
  currentLanguageInfo: typeof SUPPORTED_LANGUAGES[number]
  supportedLanguages: typeof SUPPORTED_LANGUAGES
  changeLanguage: (language: SupportedLanguage) => Promise<void>
  isChangingLanguage: boolean
  error: string | null
}

export const useLanguage = (): UseLanguageReturn => {
  const { i18n } = useTranslation()
  const [isChangingLanguage, setIsChangingLanguage] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const currentLanguage = i18n.language as SupportedLanguage
  const currentLanguageInfo = getLanguageInfo(currentLanguage)

  const handleLanguageChange = async (language: SupportedLanguage) => {
    if (language === currentLanguage) return

    setIsChangingLanguage(true)
    setError(null)

    try {
      await changeLanguage(language)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change language')
      console.error('Language change failed:', err)
    } finally {
      setIsChangingLanguage(false)
    }
  }

  // Listen for language changes from other components
  useEffect(() => {
    const handleLanguageChanged = (event: CustomEvent) => {
      setError(null)
    }

    window.addEventListener('languageChanged', handleLanguageChanged as EventListener)
    
    return () => {
      window.removeEventListener('languageChanged', handleLanguageChanged as EventListener)
    }
  }, [])

  return {
    currentLanguage,
    currentLanguageInfo,
    supportedLanguages: SUPPORTED_LANGUAGES,
    changeLanguage: handleLanguageChange,
    isChangingLanguage,
    error
  }
}

export default useLanguage