import React from 'react'
import clsx from 'clsx'
import { User } from 'lucide-react'

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  src?: string
  alt?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  variant?: 'circular' | 'rounded' | 'square'
  fallback?: string
  showFallback?: boolean
  online?: boolean
  children?: React.ReactNode
}

const sizeClasses = {
  xs: 'w-6 h-6 text-xs',
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-12 h-12 text-lg',
  xl: 'w-16 h-16 text-xl',
  '2xl': 'w-20 h-20 text-2xl',
}

const variantClasses = {
  circular: 'rounded-full',
  rounded: 'rounded-lg',
  square: 'rounded-none',
}

const onlineIndicatorSizes = {
  xs: 'w-2 h-2',
  sm: 'w-2.5 h-2.5',
  md: 'w-3 h-3',
  lg: 'w-3.5 h-3.5',
  xl: 'w-4 h-4',
  '2xl': 'w-5 h-5',
}

const Avatar: React.FC<AvatarProps> = ({
  src,
  alt,
  size = 'md',
  variant = 'circular',
  fallback,
  showFallback = true,
  online,
  className,
  children,
  ...props
}) => {
  const [imageError, setImageError] = React.useState(false)
  const [imageLoaded, setImageLoaded] = React.useState(false)
  
  const handleImageError = () => {
    setImageError(true)
  }
  
  const handleImageLoad = () => {
    setImageLoaded(true)
    setImageError(false)
  }
  
  const showImage = src && !imageError && imageLoaded
  const showFallbackContent = !showImage && (showFallback || children || fallback)
  
  // Generate initials from fallback text
  const getInitials = (text: string) => {
    return text
      .split(' ')
      .map(word => word.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  return (
    <div
      className={clsx(
        'relative inline-flex items-center justify-center overflow-hidden bg-neutral-100 dark:bg-neutral-800',
        sizeClasses[size],
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {/* Image */}
      {src && (
        <img
          src={src}
          alt={alt || 'Avatar'}
          className={clsx(
            'w-full h-full object-cover transition-opacity duration-200',
            showImage ? 'opacity-100' : 'opacity-0'
          )}
          onError={handleImageError}
          onLoad={handleImageLoad}
        />
      )}
      
      {/* Fallback Content */}
      {showFallbackContent && (
        <div
          className={clsx(
            'absolute inset-0 flex items-center justify-center bg-gradient-sparky text-white font-medium',
            !showImage ? 'opacity-100' : 'opacity-0'
          )}
        >
          {children || (
            fallback ? (
              <span>{getInitials(fallback)}</span>
            ) : (
              <User className={clsx(
                size === 'xs' ? 'w-3 h-3' :
                size === 'sm' ? 'w-4 h-4' :
                size === 'md' ? 'w-5 h-5' :
                size === 'lg' ? 'w-6 h-6' :
                size === 'xl' ? 'w-8 h-8' :
                'w-10 h-10'
              )} />
            )
          )}
        </div>
      )}
      
      {/* Online Indicator */}
      {online !== undefined && (
        <div
          className={clsx(
            'absolute -bottom-0 -right-0 rounded-full border-2 border-white dark:border-neutral-800',
            onlineIndicatorSizes[size],
            online ? 'bg-success-500' : 'bg-neutral-400'
          )}
          aria-label={online ? 'Online' : 'Offline'}
        />
      )}
    </div>
  )
}

export default Avatar