import React from 'react'
import clsx from 'clsx'
import LoadingSpinner from '../LoadingSpinner'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  loading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  fullWidth?: boolean
  children: React.ReactNode
}

const variantClasses = {
  primary: 'bg-sparky-gold hover:bg-primary-600 focus:ring-primary-500 text-black font-semibold border-transparent',
  secondary: 'bg-neutral-600 hover:bg-neutral-700 focus:ring-neutral-500 text-white border-transparent',
  outline: 'border-sparky-gold text-sparky-gold hover:bg-sparky-gold hover:text-black focus:ring-primary-500 bg-transparent',
  ghost: 'text-sparky-gold hover:bg-primary-50 focus:ring-primary-500 bg-transparent border-transparent',
  danger: 'bg-error-500 hover:bg-error-600 focus:ring-error-500 text-white border-transparent',
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-base',
  lg: 'px-6 py-3 text-lg',
  xl: 'px-8 py-4 text-xl',
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  disabled,
  className,
  children,
  ...props
}) => {
  const isDisabled = disabled || loading

  return (
    <button
      className={clsx(
        // Base styles
        'inline-flex items-center justify-center rounded-lg border font-medium transition-colors duration-200',
        'focus:outline-none focus:ring-2 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        
        // Variant styles
        variantClasses[variant],
        
        // Size styles
        sizeClasses[size],
        
        // Width
        fullWidth && 'w-full',
        
        // Custom className
        className
      )}
      disabled={isDisabled}
      aria-disabled={isDisabled}
      {...props}
    >
      {loading && (
        <LoadingSpinner 
          size={size === 'sm' ? 'sm' : 'md'} 
          color={variant === 'outline' || variant === 'ghost' ? 'primary' : 'white'}
          className="mr-2"
        />
      )}
      
      {!loading && leftIcon && (
        <span className="mr-2 flex-shrink-0">
          {leftIcon}
        </span>
      )}
      
      <span className="flex-1">
        {children}
      </span>
      
      {!loading && rightIcon && (
        <span className="ml-2 flex-shrink-0">
          {rightIcon}
        </span>
      )}
    </button>
  )
}

export default Button