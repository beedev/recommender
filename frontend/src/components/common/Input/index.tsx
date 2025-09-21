import React, { forwardRef } from 'react'
import clsx from 'clsx'
import { AlertCircle, Eye, EyeOff } from 'lucide-react'

interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string
  error?: string
  helperText?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'error' | 'success'
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  fullWidth?: boolean
  showPasswordToggle?: boolean
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-4 py-3 text-lg',
}

const variantClasses = {
  default: 'border-neutral-300 focus:border-primary-500 focus:ring-primary-500',
  error: 'border-error-300 focus:border-error-500 focus:ring-error-500',
  success: 'border-success-300 focus:border-success-500 focus:ring-success-500',
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  helperText,
  size = 'md',
  variant = 'default',
  leftIcon,
  rightIcon,
  fullWidth = false,
  showPasswordToggle = false,
  className,
  disabled,
  type = 'text',
  id,
  ...props
}, ref) => {
  const [showPassword, setShowPassword] = React.useState(false)
  const [inputType, setInputType] = React.useState(type)
  
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`
  const errorId = error ? `${inputId}-error` : undefined
  const helperTextId = helperText ? `${inputId}-helper` : undefined
  
  // Handle password visibility toggle
  React.useEffect(() => {
    if (showPasswordToggle && type === 'password') {
      setInputType(showPassword ? 'text' : 'password')
    } else {
      setInputType(type)
    }
  }, [showPassword, showPasswordToggle, type])
  
  const actualVariant = error ? 'error' : variant
  const hasLeftIcon = leftIcon || (error && variant !== 'error')
  const hasRightIcon = rightIcon || (showPasswordToggle && type === 'password')

  return (
    <div className={clsx('flex flex-col', fullWidth ? 'w-full' : 'w-auto')}>
      {/* Label */}
      {label && (
        <label
          htmlFor={inputId}
          className="mb-1 text-sm font-medium text-neutral-700 dark:text-neutral-300"
        >
          {label}
        </label>
      )}
      
      {/* Input Container */}
      <div className="relative">
        {/* Left Icon */}
        {hasLeftIcon && (
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            {error && variant !== 'error' ? (
              <AlertCircle className="w-5 h-5 text-error-500" />
            ) : (
              leftIcon
            )}
          </div>
        )}
        
        {/* Input */}
        <input
          ref={ref}
          type={inputType}
          id={inputId}
          className={clsx(
            // Base styles
            'block w-full rounded-lg border bg-white shadow-sm transition-colors duration-200',
            'placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-offset-0',
            'disabled:bg-neutral-50 disabled:text-neutral-500 disabled:cursor-not-allowed',
            'dark:bg-neutral-800 dark:border-neutral-600 dark:text-white dark:placeholder:text-neutral-500',
            
            // Size styles
            sizeClasses[size],
            
            // Variant styles
            variantClasses[actualVariant],
            
            // Icon padding
            hasLeftIcon && 'pl-10',
            hasRightIcon && 'pr-10',
            
            // Custom className
            className
          )}
          disabled={disabled}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={clsx(errorId, helperTextId).trim() || undefined}
          {...props}
        />
        
        {/* Right Icon */}
        {hasRightIcon && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            {showPasswordToggle && type === 'password' ? (
              <button
                type="button"
                className="text-neutral-400 hover:text-neutral-600 focus:outline-none focus:text-neutral-600 transition-colors"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            ) : (
              rightIcon
            )}
          </div>
        )}
      </div>
      
      {/* Error Message */}
      {error && (
        <p
          id={errorId}
          className="mt-1 text-sm text-error-600 dark:text-error-400"
          role="alert"
        >
          {error}
        </p>
      )}
      
      {/* Helper Text */}
      {helperText && !error && (
        <p
          id={helperTextId}
          className="mt-1 text-sm text-neutral-500 dark:text-neutral-400"
        >
          {helperText}
        </p>
      )}
    </div>
  )
})

Input.displayName = 'Input'

export default Input