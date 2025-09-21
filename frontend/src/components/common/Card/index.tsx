import React from 'react'
import clsx from 'clsx'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined' | 'elevated' | 'glass'
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  rounded?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  shadow?: 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'esab'
  hover?: boolean
  interactive?: boolean
  children: React.ReactNode
}

const variantClasses = {
  default: 'bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700',
  outlined: 'bg-transparent border-2 border-neutral-300 dark:border-neutral-600',
  elevated: 'bg-white dark:bg-neutral-800 border-0',
  glass: 'bg-white/80 dark:bg-neutral-800/80 backdrop-blur-md border border-white/20 dark:border-neutral-700/20',
}

const paddingClasses = {
  none: 'p-0',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8',
}

const roundedClasses = {
  none: 'rounded-none',
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  '2xl': 'rounded-2xl',
}

const shadowClasses = {
  none: 'shadow-none',
  sm: 'shadow-sm',
  md: 'shadow-md',
  lg: 'shadow-lg',
  xl: 'shadow-xl',
  esab: 'shadow-esab',
}

const Card: React.FC<CardProps> = ({
  variant = 'default',
  padding = 'md',
  rounded = 'lg',
  shadow = 'md',
  hover = false,
  interactive = false,
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={clsx(
        // Base styles
        'transition-all duration-200',
        
        // Variant styles
        variantClasses[variant],
        
        // Padding styles
        paddingClasses[padding],
        
        // Rounded styles
        roundedClasses[rounded],
        
        // Shadow styles
        shadowClasses[shadow],
        
        // Hover effects
        hover && 'hover:shadow-lg hover:-translate-y-0.5',
        
        // Interactive styles
        interactive && [
          'cursor-pointer',
          'hover:shadow-lg hover:-translate-y-0.5',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          'active:translate-y-0',
        ],
        
        // Custom className
        className
      )}
      tabIndex={interactive ? 0 : undefined}
      role={interactive ? 'button' : undefined}
      {...props}
    >
      {children}
    </div>
  )
}

// Card sub-components
interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const CardHeader: React.FC<CardHeaderProps> = ({ className, children, ...props }) => (
  <div
    className={clsx(
      'flex flex-col space-y-1.5 pb-4',
      className
    )}
    {...props}
  >
    {children}
  </div>
)

interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'
  children: React.ReactNode
}

const CardTitle: React.FC<CardTitleProps> = ({ 
  as: Component = 'h3', 
  className, 
  children, 
  ...props 
}) => (
  <Component
    className={clsx(
      'text-lg font-semibold leading-none tracking-tight text-neutral-900 dark:text-neutral-100',
      className
    )}
    {...props}
  >
    {children}
  </Component>
)

interface CardDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode
}

const CardDescription: React.FC<CardDescriptionProps> = ({ className, children, ...props }) => (
  <p
    className={clsx(
      'text-sm text-neutral-600 dark:text-neutral-400',
      className
    )}
    {...props}
  >
    {children}
  </p>
)

interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const CardContent: React.FC<CardContentProps> = ({ className, children, ...props }) => (
  <div
    className={clsx('pt-0', className)}
    {...props}
  >
    {children}
  </div>
)

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
}

const CardFooter: React.FC<CardFooterProps> = ({ className, children, ...props }) => (
  <div
    className={clsx(
      'flex items-center pt-4',
      className
    )}
    {...props}
  >
    {children}
  </div>
)

// Create a compound component with proper typing
interface CardComponent extends React.FC<CardProps> {
  Header: typeof CardHeader
  Title: typeof CardTitle
  Description: typeof CardDescription
  Content: typeof CardContent
  Footer: typeof CardFooter
}

// Attach sub-components to main Card component
const CardWithSubComponents = Card as CardComponent
CardWithSubComponents.Header = CardHeader
CardWithSubComponents.Title = CardTitle
CardWithSubComponents.Description = CardDescription
CardWithSubComponents.Content = CardContent
CardWithSubComponents.Footer = CardFooter

export default CardWithSubComponents