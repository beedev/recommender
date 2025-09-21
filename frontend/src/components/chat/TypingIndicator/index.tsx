import React from 'react'
import { Zap } from 'lucide-react'

interface TypingIndicatorProps {
  className?: string
  message?: string
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  className = '',
  message = 'Sparky is thinking...'
}) => {
  return (
    <div className={`flex items-start gap-3 ${className}`}>
      <div className="sparky-avatar w-8 h-8 text-sm flex-shrink-0">
        <Zap className="w-4 h-4" />
      </div>
      
      <div className="bg-white text-gray-800 border border-gray-200 rounded-lg px-4 py-2 max-w-md">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">{message}</span>
          <div className="flex gap-1">
            <div className="w-2 h-2 bg-sparky-gold rounded-full animate-bounce"></div>
            <div 
              className="w-2 h-2 bg-sparky-gold rounded-full animate-bounce" 
              style={{ animationDelay: '0.1s' }}
            ></div>
            <div 
              className="w-2 h-2 bg-sparky-gold rounded-full animate-bounce" 
              style={{ animationDelay: '0.2s' }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TypingIndicator