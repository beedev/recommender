import { SupportedLanguage } from '../../locales/i18n'

export interface LanguagePreferences {
  language: SupportedLanguage
  autoDetect: boolean
  fallbackLanguage: SupportedLanguage
}

export class LanguageService {
  private static readonly STORAGE_KEY = 'language_preferences'
  private static readonly API_HEADER = 'Accept-Language'

  /**
   * Get user's language preferences from localStorage
   */
  static getPreferences(): LanguagePreferences {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY)
      if (stored) {
        return JSON.parse(stored)
      }
    } catch (error) {
      console.warn('Failed to parse language preferences:', error)
    }

    // Default preferences
    return {
      language: 'en',
      autoDetect: true,
      fallbackLanguage: 'en'
    }
  }

  /**
   * Save user's language preferences to localStorage
   */
  static savePreferences(preferences: LanguagePreferences): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(preferences))
    } catch (error) {
      console.error('Failed to save language preferences:', error)
    }
  }

  /**
   * Update the current language preference
   */
  static updateLanguage(language: SupportedLanguage): void {
    const preferences = this.getPreferences()
    preferences.language = language
    this.savePreferences(preferences)
  }

  /**
   * Get the Accept-Language header value for API requests
   */
  static getAcceptLanguageHeader(language?: SupportedLanguage): string {
    const currentLanguage = language || this.getPreferences().language
    const preferences = this.getPreferences()
    
    // Format: en-US,en;q=0.9,es;q=0.8
    return `${currentLanguage};q=1.0,${preferences.fallbackLanguage};q=0.8,en;q=0.6`
  }

  /**
   * Add language header to fetch request options
   */
  static addLanguageHeaders(options: RequestInit = {}, language?: SupportedLanguage): RequestInit {
    const headers = new Headers(options.headers)
    headers.set(this.API_HEADER, this.getAcceptLanguageHeader(language))
    
    return {
      ...options,
      headers
    }
  }

  /**
   * Create a fetch wrapper that automatically includes language headers
   */
  static createLanguageAwareFetch(language?: SupportedLanguage) {
    return (url: string | URL | Request, options?: RequestInit) => {
      const enhancedOptions = this.addLanguageHeaders(options, language)
      return fetch(url, enhancedOptions)
    }
  }

  /**
   * Detect browser language and return supported language or fallback
   */
  static detectBrowserLanguage(): SupportedLanguage {
    const supportedLanguages: SupportedLanguage[] = ['en', 'es', 'fr', 'de']
    
    // Check navigator.languages first (most preferred)
    if (navigator.languages) {
      for (const lang of navigator.languages) {
        const baseLanguage = lang.split('-')[0].toLowerCase() as SupportedLanguage
        if (supportedLanguages.includes(baseLanguage)) {
          return baseLanguage
        }
      }
    }
    
    // Fallback to navigator.language
    if (navigator.language) {
      const baseLanguage = navigator.language.split('-')[0].toLowerCase() as SupportedLanguage
      if (supportedLanguages.includes(baseLanguage)) {
        return baseLanguage
      }
    }
    
    // Final fallback
    return 'en'
  }

  /**
   * Initialize language based on preferences and browser detection
   */
  static initializeLanguage(): SupportedLanguage {
    const preferences = this.getPreferences()
    
    if (preferences.autoDetect) {
      const detectedLanguage = this.detectBrowserLanguage()
      if (detectedLanguage !== preferences.language) {
        this.updateLanguage(detectedLanguage)
        return detectedLanguage
      }
    }
    
    return preferences.language
  }

  /**
   * Format numbers according to the current language locale
   */
  static formatNumber(
    value: number, 
    language: SupportedLanguage, 
    options?: Intl.NumberFormatOptions
  ): string {
    const localeMap: Record<SupportedLanguage, string> = {
      en: 'en-US',
      es: 'es-ES',
      fr: 'fr-FR',
      de: 'de-DE'
    }
    
    return new Intl.NumberFormat(localeMap[language], options).format(value)
  }

  /**
   * Format currency according to the current language locale
   */
  static formatCurrency(
    value: number, 
    language: SupportedLanguage, 
    currency: string = 'USD'
  ): string {
    return this.formatNumber(value, language, {
      style: 'currency',
      currency
    })
  }

  /**
   * Format dates according to the current language locale
   */
  static formatDate(
    date: Date, 
    language: SupportedLanguage, 
    options?: Intl.DateTimeFormatOptions
  ): string {
    const localeMap: Record<SupportedLanguage, string> = {
      en: 'en-US',
      es: 'es-ES',
      fr: 'fr-FR',
      de: 'de-DE'
    }
    
    return new Intl.DateTimeFormat(localeMap[language], options).format(date)
  }
}

export default LanguageService