import React, { forwardRef } from 'react'
import clsx from 'clsx'
import { AlertCircle } from 'lucide-react'

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'error' | 'success'
  fullWidth?: boolean
  resize?: 'none' | 'vertical' | 'horizontal' | 'both'
  autoResize?: boolean
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

const resizeClasses = {
  none: 'resize-none',
  vertical: 'resize-y',
  horizontal: 'resize-x',
  both: 'resize',
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(({
  label,
  error,
  helperText,
  size = 'md',
  variant = 'default',
  fullWidth = false,
  resize = 'vertical',
  autoResize = false,
  className,
  disabled,
  id,
  rows = 4,
  ...props
}, ref) => {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null)
  const inputId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`
  const errorId = error ? `${inputId}-error` : undefined
  const helperTextId = helperText ? `${inputId}-helper` : undefined
  
  const actualVariant = error ? 'error' : variant
  
  // Auto-resize functionality
  const handleAutoResize = React.useCallback(() => {
    const textarea = textareaRef.current
    if (textarea && autoResize) {
      textarea.style.height = 'auto'
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }, [autoResize])
  
  React.useEffect(() => {
    if (autoResize) {
      handleAutoResize()
    }
  }, [handleAutoResize, props.value])
  
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (autoResize) {
      handleAutoResize()
    }
    props.onChange?.(e)
  }

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
      
      {/* Textarea Container */}
      <div className="relative">
        {/* Error Icon */}
        {error && (
          <div className="absolute top-3 right-3 pointer-events-none">
            <AlertCircle className="w-5 h-5 text-error-500" />
          </div>
        )}
        
        {/* Textarea */}
        <textarea
          ref={(node) => {
            // Update the internal ref
            if (textareaRef.current !== node) {
              (textareaRef as React.MutableRefObject<HTMLTextAreaElement | null>).current = node
            }
            // Forward the ref
            if (typeof ref === 'function') {
              ref(node)
            } else if (ref) {
              (ref as React.MutableRefObject<HTMLTextAreaElement | null>).current = node
            }
          }}
          id={inputId}
          rows={rows}
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
            
            // Resize styles
            resizeClasses[resize],
            
            // Error padding
            error && 'pr-10',
            
            // Custom className
            className
          )}
          disabled={disabled}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={clsx(errorId, helperTextId).trim() || undefined}
          {...props}
          onChange={handleChange}
        />
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

Textarea.displayName = 'Textarea'

export default Textarea