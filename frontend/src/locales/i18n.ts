import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

// Import translation files
import enCommon from './en/common.json'
import enNavigation from './en/navigation.json'
import enSparky from './en/sparky.json'
import enAuth from './en/auth.json'
import enInventory from './en/inventory.json'
import enErrors from './en/errors.json'

import esCommon from './es/common.json'
import esNavigation from './es/navigation.json'
import esSparky from './es/sparky.json'
import esAuth from './es/auth.json'
import esInventory from './es/inventory.json'
import esErrors from './es/errors.json'

import frCommon from './fr/common.json'
import frNavigation from './fr/navigation.json'
import frSparky from './fr/sparky.json'
import frAuth from './fr/auth.json'
import frInventory from './fr/inventory.json'
import frErrors from './fr/errors.json'

import deCommon from './de/common.json'
import deNavigation from './de/navigation.json'
import deSparky from './de/sparky.json'
import deAuth from './de/auth.json'
import deInventory from './de/inventory.json'
import deErrors from './de/errors.json'

// Define resources
const resources = {
  en: {
    common: enCommon,
    navigation: enNavigation,
    sparky: enSparky,
    auth: enAuth,
    inventory: enInventory,
    errors: enErrors,
  },
  es: {
    common: esCommon,
    navigation: esNavigation,
    sparky: esSparky,
    auth: esAuth,
    inventory: esInventory,
    errors: esErrors,
  },
  fr: {
    common: frCommon,
    navigation: frNavigation,
    sparky: frSparky,
    auth: frAuth,
    inventory: frInventory,
    errors: frErrors,
  },
  de: {
    common: deCommon,
    navigation: deNavigation,
    sparky: deSparky,
    auth: deAuth,
    inventory: deInventory,
    errors: deErrors,
  },
} as const

// Configure i18next
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    lng: 'en', // Fixed 2025-01-09: Explicitly set default language to English
    debug: import.meta.env.DEV,

    // Language detection options
    // Fixed 2025-01-09: Force English as default and reduce detection priority
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
      lookupLocalStorage: 'language',
      // Convert regional codes to base language codes
      convertDetectedLanguage: (lng: string) => {
        // Convert en-US, en-IN, en-GB, etc. to just 'en'
        // Convert es-ES, es-MX, etc. to just 'es'
        // Convert fr-FR, fr-CA, etc. to just 'fr'
        // Convert de-DE, de-AT, etc. to just 'de'
        const baseLanguage = lng?.split('-')[0]?.toLowerCase() || 'en'
        const supportedLanguages = ['en', 'es', 'fr', 'de']
        return supportedLanguages.includes(baseLanguage) ? baseLanguage : 'en'
      },
    },

    interpolation: {
      escapeValue: false, // React already escapes values
    },

    // Namespace configuration
    defaultNS: 'common',
    ns: ['common', 'navigation', 'sparky', 'auth', 'inventory', 'errors'],

    // React-specific options
    react: {
      useSuspense: true,
      transEmptyNodeValue: '', // Return empty string for empty translations
      transSupportBasicHtmlNodes: true, // Allow basic HTML tags
      transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'em'], // Allowed HTML tags
    },

    // Backend options for development
    backend: {
      loadPath: '/locales/{{lng}}/{{ns}}.json',
    },

    // Pluralization options
    pluralSeparator: '_',
    contextSeparator: '_',

    // Performance options
    load: 'languageOnly', // Don't load country-specific variants
    preload: ['en', 'es', 'fr', 'de'],
    
    // Handle regional variants gracefully
    cleanCode: true, // Remove script and region from language code (en-IN becomes en)

    // Custom options
    returnNull: false, // Return key instead of null for missing translations
    returnEmptyString: false, // Return key instead of empty string
    
    // Formatting
    postProcess: ['interval'], // Enable interval plurals
  })

// Export type-safe translation function
export default i18n

// Export supported languages
export const SUPPORTED_LANGUAGES = [
  {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇺🇸',
    dir: 'ltr'
  },
  {
    code: 'es',
    name: 'Spanish',
    nativeName: 'Español',
    flag: '🇪🇸',
    dir: 'ltr'
  },
  {
    code: 'fr',
    name: 'French',
    nativeName: 'Français',
    flag: '🇫🇷',
    dir: 'ltr'
  },
  {
    code: 'de',
    name: 'German',
    nativeName: 'Deutsch',
    flag: '🇩🇪',
    dir: 'ltr'
  },
] as const

export type SupportedLanguage = typeof SUPPORTED_LANGUAGES[number]['code']

// Helper function to get language info
export const getLanguageInfo = (code: string) => {
  return SUPPORTED_LANGUAGES.find(lang => lang.code === code) || SUPPORTED_LANGUAGES[0]
}

// Helper function to change language
export const changeLanguage = async (language: SupportedLanguage) => {
  await i18n.changeLanguage(language)
  localStorage.setItem('language', language)
  
  // Update document language
  document.documentElement.lang = language
  
  // Update page direction based on language
  const languageInfo = getLanguageInfo(language)
  document.documentElement.dir = languageInfo.dir
  
  // Dispatch custom event for other components to react to language change
  window.dispatchEvent(new CustomEvent('languageChanged', { 
    detail: { language, languageInfo } 
  }))
}