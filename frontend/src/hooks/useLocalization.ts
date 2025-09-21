import { useCallback } from 'react'
import { useLanguage } from './useLanguage'
import {
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
} from '../utils/localization'
import { SupportedLanguage } from '../locales/i18n'

interface UseLocalizationReturn {
  // Current language
  currentLanguage: SupportedLanguage
  
  // Formatting functions (bound to current language)
  formatCurrency: (amount: number, currency?: string, options?: Intl.NumberFormatOptions) => string
  formatNumber: (value: number, options?: Intl.NumberFormatOptions) => string
  formatPercentage: (value: number, options?: Intl.NumberFormatOptions) => string
  formatDate: (date: Date | string | number, options?: Intl.DateTimeFormatOptions) => string
  formatTime: (date: Date | string | number, options?: Intl.DateTimeFormatOptions) => string
  formatRelativeTime: (date: Date | string | number, options?: Intl.RelativeTimeFormatOptions) => string
  formatFileSize: (bytes: number, options?: { binary?: boolean }) => string
  formatTechnicalSpec: (value: number, unit: string, options?: Intl.NumberFormatOptions) => string
  formatVoltageRange: (min: number, max: number) => string
  formatCurrentRange: (min: number, max: number) => string
  
  // Parsing functions
  parseLocalizedNumber: (value: string) => number | null
  
  // Utility functions
  getDecimalSeparator: () => string
  getThousandsSeparator: () => string
  
  // Validation functions
  isValidNumber: (value: string) => boolean
  isValidCurrency: (value: string) => boolean
}

export const useLocalization = (): UseLocalizationReturn => {
  const { currentLanguage } = useLanguage()

  // Bound formatting functions
  const boundFormatCurrency = useCallback(
    (amount: number, currency?: string, options?: Intl.NumberFormatOptions) =>
      formatCurrency(amount, currentLanguage, currency, options),
    [currentLanguage]
  )

  const boundFormatNumber = useCallback(
    (value: number, options?: Intl.NumberFormatOptions) =>
      formatNumber(value, currentLanguage, options),
    [currentLanguage]
  )

  const boundFormatPercentage = useCallback(
    (value: number, options?: Intl.NumberFormatOptions) =>
      formatPercentage(value, currentLanguage, options),
    [currentLanguage]
  )

  const boundFormatDate = useCallback(
    (date: Date | string | number, options?: Intl.DateTimeFormatOptions) =>
      formatDate(date, currentLanguage, options),
    [currentLanguage]
  )

  const boundFormatTime = useCallback(
    (date: Date | string | number, options?: Intl.DateTimeFormatOptions) =>
      formatTime(date, currentLanguage, options),
    [currentLanguage]
  )

  const boundFormatRelativeTime = useCallback(
    (date: Date | string | number, options?: Intl.RelativeTimeFormatOptions) =>
      formatRelativeTime(date, currentLanguage, options),
    [currentLanguage]
  )

  const boundFormatFileSize = useCallback(
    (bytes: number, options?: { binary?: boolean }) =>
      formatFileSize(bytes, currentLanguage, options),
    [currentLanguage]
  )

  const boundFormatTechnicalSpec = useCallback(
    (value: number, unit: string, options?: Intl.NumberFormatOptions) =>
      formatTechnicalSpec(value, unit, currentLanguage, options),
    [currentLanguage]
  )

  const boundFormatVoltageRange = useCallback(
    (min: number, max: number) =>
      formatVoltageRange(min, max, currentLanguage),
    [currentLanguage]
  )

  const boundFormatCurrentRange = useCallback(
    (min: number, max: number) =>
      formatCurrentRange(min, max, currentLanguage),
    [currentLanguage]
  )

  const boundParseLocalizedNumber = useCallback(
    (value: string) =>
      parseLocalizedNumber(value, currentLanguage),
    [currentLanguage]
  )

  const boundGetDecimalSeparator = useCallback(
    () => getDecimalSeparator(currentLanguage),
    [currentLanguage]
  )

  const boundGetThousandsSeparator = useCallback(
    () => getThousandsSeparator(currentLanguage),
    [currentLanguage]
  )

  // Validation functions
  const isValidNumber = useCallback(
    (value: string): boolean => {
      const parsed = boundParseLocalizedNumber(value)
      return parsed !== null && !isNaN(parsed)
    },
    [boundParseLocalizedNumber]
  )

  const isValidCurrency = useCallback(
    (value: string): boolean => {
      // Remove currency symbols and whitespace
      const cleaned = value.replace(/[^\d.,\-+]/g, '')
      return isValidNumber(cleaned)
    },
    [isValidNumber]
  )

  return {
    currentLanguage,
    formatCurrency: boundFormatCurrency,
    formatNumber: boundFormatNumber,
    formatPercentage: boundFormatPercentage,
    formatDate: boundFormatDate,
    formatTime: boundFormatTime,
    formatRelativeTime: boundFormatRelativeTime,
    formatFileSize: boundFormatFileSize,
    formatTechnicalSpec: boundFormatTechnicalSpec,
    formatVoltageRange: boundFormatVoltageRange,
    formatCurrentRange: boundFormatCurrentRange,
    parseLocalizedNumber: boundParseLocalizedNumber,
    getDecimalSeparator: boundGetDecimalSeparator,
    getThousandsSeparator: boundGetThousandsSeparator,
    isValidNumber,
    isValidCurrency
  }
}

export default useLocalization