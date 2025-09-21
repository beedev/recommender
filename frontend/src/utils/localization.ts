import { SupportedLanguage } from '../locales/i18n'

// Locale mapping for Intl APIs
const LOCALE_MAP: Record<SupportedLanguage, string> = {
  en: 'en-US',
  es: 'es-ES',
  fr: 'fr-FR',
  de: 'de-DE'
}

// Currency mapping by region
const CURRENCY_MAP: Record<SupportedLanguage, string> = {
  en: 'USD',
  es: 'EUR',
  fr: 'EUR',
  de: 'EUR'
}

// Regional number formatting preferences
const NUMBER_FORMAT_OPTIONS: Record<SupportedLanguage, Intl.NumberFormatOptions> = {
  en: {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  },
  es: {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  },
  fr: {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  },
  de: {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }
}

/**
 * Format currency according to locale
 */
export const formatCurrency = (
  amount: number,
  language: SupportedLanguage,
  currency?: string,
  options?: Intl.NumberFormatOptions
): string => {
  const locale = LOCALE_MAP[language]
  const defaultCurrency = currency || CURRENCY_MAP[language]
  
  const formatOptions: Intl.NumberFormatOptions = {
    style: 'currency',
    currency: defaultCurrency,
    ...NUMBER_FORMAT_OPTIONS[language],
    ...options
  }
  
  try {
    return new Intl.NumberFormat(locale, formatOptions).format(amount)
  } catch (error) {
    console.warn('Currency formatting failed:', error)
    // Fallback to English formatting
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount)
  }
}

/**
 * Format numbers according to locale
 */
export const formatNumber = (
  value: number,
  language: SupportedLanguage,
  options?: Intl.NumberFormatOptions
): string => {
  const locale = LOCALE_MAP[language]
  
  const formatOptions: Intl.NumberFormatOptions = {
    ...NUMBER_FORMAT_OPTIONS[language],
    ...options
  }
  
  try {
    return new Intl.NumberFormat(locale, formatOptions).format(value)
  } catch (error) {
    console.warn('Number formatting failed:', error)
    // Fallback to English formatting
    return new Intl.NumberFormat('en-US').format(value)
  }
}

/**
 * Format percentage according to locale
 */
export const formatPercentage = (
  value: number,
  language: SupportedLanguage,
  options?: Intl.NumberFormatOptions
): string => {
  const locale = LOCALE_MAP[language]
  
  const formatOptions: Intl.NumberFormatOptions = {
    style: 'percent',
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
    ...options
  }
  
  try {
    return new Intl.NumberFormat(locale, formatOptions).format(value / 100)
  } catch (error) {
    console.warn('Percentage formatting failed:', error)
    return `${value.toFixed(1)}%`
  }
}

/**
 * Format dates according to locale
 */
export const formatDate = (
  date: Date | string | number,
  language: SupportedLanguage,
  options?: Intl.DateTimeFormatOptions
): string => {
  const locale = LOCALE_MAP[language]
  const dateObj = new Date(date)
  
  if (isNaN(dateObj.getTime())) {
    console.warn('Invalid date provided to formatDate')
    return 'Invalid Date'
  }
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }
  
  const formatOptions = { ...defaultOptions, ...options }
  
  try {
    return new Intl.DateTimeFormat(locale, formatOptions).format(dateObj)
  } catch (error) {
    console.warn('Date formatting failed:', error)
    // Fallback to ISO string
    return dateObj.toLocaleDateString('en-US')
  }
}

/**
 * Format time according to locale
 */
export const formatTime = (
  date: Date | string | number,
  language: SupportedLanguage,
  options?: Intl.DateTimeFormatOptions
): string => {
  const locale = LOCALE_MAP[language]
  const dateObj = new Date(date)
  
  if (isNaN(dateObj.getTime())) {
    console.warn('Invalid date provided to formatTime')
    return 'Invalid Time'
  }
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit'
  }
  
  const formatOptions = { ...defaultOptions, ...options }
  
  try {
    return new Intl.DateTimeFormat(locale, formatOptions).format(dateObj)
  } catch (error) {
    console.warn('Time formatting failed:', error)
    // Fallback to simple format
    return dateObj.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export const formatRelativeTime = (
  date: Date | string | number,
  language: SupportedLanguage,
  options?: Intl.RelativeTimeFormatOptions
): string => {
  const locale = LOCALE_MAP[language]
  const dateObj = new Date(date)
  const now = new Date()
  
  if (isNaN(dateObj.getTime())) {
    console.warn('Invalid date provided to formatRelativeTime')
    return 'Invalid Date'
  }
  
  const diffInSeconds = (dateObj.getTime() - now.getTime()) / 1000
  const diffInMinutes = diffInSeconds / 60
  const diffInHours = diffInMinutes / 60
  const diffInDays = diffInHours / 24
  
  try {
    const rtf = new Intl.RelativeTimeFormat(locale, {
      numeric: 'auto',
      style: 'long',
      ...options
    })
    
    if (Math.abs(diffInDays) >= 1) {
      return rtf.format(Math.round(diffInDays), 'day')
    } else if (Math.abs(diffInHours) >= 1) {
      return rtf.format(Math.round(diffInHours), 'hour')
    } else if (Math.abs(diffInMinutes) >= 1) {
      return rtf.format(Math.round(diffInMinutes), 'minute')
    } else {
      return rtf.format(Math.round(diffInSeconds), 'second')
    }
  } catch (error) {
    console.warn('Relative time formatting failed:', error)
    // Fallback to simple format
    return formatDate(dateObj, language)
  }
}

/**
 * Format file sizes according to locale
 */
export const formatFileSize = (
  bytes: number,
  language: SupportedLanguage,
  options?: { binary?: boolean }
): string => {
  const binary = options?.binary ?? false
  const base = binary ? 1024 : 1000
  const units = binary 
    ? ['B', 'KiB', 'MiB', 'GiB', 'TiB'] 
    : ['B', 'KB', 'MB', 'GB', 'TB']
  
  if (bytes === 0) return `0 ${units[0]}`
  
  const exponent = Math.floor(Math.log(bytes) / Math.log(base))
  const value = bytes / Math.pow(base, exponent)
  const unit = units[Math.min(exponent, units.length - 1)]
  
  const formattedValue = formatNumber(value, language, {
    minimumFractionDigits: 0,
    maximumFractionDigits: exponent === 0 ? 0 : 1
  })
  
  return `${formattedValue} ${unit}`
}

/**
 * Get decimal separator for a language
 */
export const getDecimalSeparator = (language: SupportedLanguage): string => {
  const locale = LOCALE_MAP[language]
  
  try {
    const formatted = new Intl.NumberFormat(locale).format(1.1)
    return formatted.charAt(1) // The character between 1 and 1
  } catch (error) {
    return '.' // Fallback to period
  }
}

/**
 * Get thousands separator for a language
 */
export const getThousandsSeparator = (language: SupportedLanguage): string => {
  const locale = LOCALE_MAP[language]
  
  try {
    const formatted = new Intl.NumberFormat(locale).format(1000)
    return formatted.charAt(1) // The character between 1 and 000
  } catch (error) {
    return ',' // Fallback to comma
  }
}

/**
 * Parse localized number string back to number
 */
export const parseLocalizedNumber = (
  value: string,
  language: SupportedLanguage
): number | null => {
  if (!value || typeof value !== 'string') return null
  
  const decimalSeparator = getDecimalSeparator(language)
  const thousandsSeparator = getThousandsSeparator(language)
  
  // Remove thousands separators and replace decimal separator with period
  let normalized = value
    .replace(new RegExp(`\\${thousandsSeparator}`, 'g'), '')
    .replace(decimalSeparator, '.')
  
  // Remove any non-numeric characters except period and minus
  normalized = normalized.replace(/[^0-9.-]/g, '')
  
  const parsed = parseFloat(normalized)
  return isNaN(parsed) ? null : parsed
}

/**
 * Format technical specifications with proper units
 */
export const formatTechnicalSpec = (
  value: number,
  unit: string,
  language: SupportedLanguage,
  options?: Intl.NumberFormatOptions
): string => {
  const formattedValue = formatNumber(value, language, options)
  
  // Technical units are typically not translated
  return `${formattedValue} ${unit}`
}

/**
 * Format voltage range
 */
export const formatVoltageRange = (
  min: number,
  max: number,
  language: SupportedLanguage
): string => {
  const formattedMin = formatNumber(min, language, { maximumFractionDigits: 0 })
  const formattedMax = formatNumber(max, language, { maximumFractionDigits: 0 })
  
  return `${formattedMin}-${formattedMax}V`
}

/**
 * Format current range
 */
export const formatCurrentRange = (
  min: number,
  max: number,
  language: SupportedLanguage
): string => {
  const formattedMin = formatNumber(min, language, { maximumFractionDigits: 0 })
  const formattedMax = formatNumber(max, language, { maximumFractionDigits: 0 })
  
  return `${formattedMin}-${formattedMax}A`
}

export default {
  formatCurrency,
  formatNumber,
  formatPercentage,
  formatDate,
  formatTime,
  formatRelativeTime,
  formatFileSize,
  formatTechnicalSpec,
  formatVoltageRange,
  formatCurrentRange,
  parseLocalizedNumber,
  getDecimalSeparator,
  getThousandsSeparator
}