import React from 'react'
import clsx from 'clsx'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  rounded?: boolean
  dot?: boolean
  children: React.ReactNode
}

const variantClasses = {
  default: 'bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200',
  primary: 'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200',
  secondary: 'bg-neutral-100 text-neutral-800 dark:bg-neutral-700 dark:text-neutral-200',
  success: 'bg-success-100 text-success-800 dark:bg-success-900 dark:text-success-200',
  warning: 'bg-warning-100 text-warning-800 dark:bg-warning-900 dark:text-warning-200',
  error: 'bg-error-100 text-error-800 dark:bg-error-900 dark:text-error-200',
  info: 'bg-info-100 text-info-800 dark:bg-info-900 dark:text-info-200',
  outline: 'border border-neutral-300 text-neutral-700 dark:border-neutral-600 dark:text-neutral-300',
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
}

const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'md',
  rounded = false,
  dot = false,
  className,
  children,
  ...props
}) => {
  if (dot) {
    return (
      <span
        className={clsx(
          'inline-flex items-center gap-1.5',
          className
        )}
        {...props}
      >
        <span
          className={clsx(
            'w-2 h-2 rounded-full',
            variantClasses[variant].split(' ')[0] // Get background color class
          )}
        />
        <span className="text-sm font-medium">{children}</span>
      </span>
    )
  }

  return (
    <span
      className={clsx(
        // Base styles
        'inline-flex items-center font-medium',
        
        // Variant styles
        variantClasses[variant],
        
        // Size styles
        sizeClasses[size],
        
        // Rounded styles
        rounded ? 'rounded-full' : 'rounded-md',
        
        // Custom className
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}

export default Badge