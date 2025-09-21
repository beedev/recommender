import React from 'react'
import { Zap, User, Clock, AlertCircle } from 'lucide-react'
import { EnhancedChatMessage } from '../../../types/enhanced-orchestrator'
import { 
  formatMessageContent, 
  formatTimestamp, 
  formatConfidenceScore,
  getMessageDisplayClass 
} from '../../../utils/messageFormatting'

interface MessageBubbleProps {
  message: EnhancedChatMessage
  className?: string
  showTimestamp?: boolean
  showMetadata?: boolean
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  className = '',
  showTimestamp = false,
  showMetadata = true
}) => {
  const isUser = message.sender === 'user'
  const isSparky = message.sender === 'sparky'
  const hasError = message.metadata?.error
  const isLowConfidence = message.metadata?.confidence && message.metadata.confidence < 0.5

  const displayClass = getMessageDisplayClass(message)
  const formattedContent = formatMessageContent(message)

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'justify-end' : ''} ${className}`}>
      {/* Avatar for Sparky messages */}
      {isSparky && (
        <div className={`sparky-avatar w-8 h-8 text-sm flex-shrink-0 ${hasError ? 'opacity-50' : ''}`}>
          {hasError ? (
            <AlertCircle className="w-4 h-4 text-red-500" />
          ) : (
            <Zap className="w-4 h-4" />
          )}
        </div>
      )}
      
      {/* Message Content */}
      <div className={`max-w-md rounded-lg px-4 py-2 ${displayClass} ${
        isUser 
          ? 'bg-sparky-gold text-black ml-auto' 
          : hasError
            ? 'bg-red-50 text-red-800 border border-red-200'
            : isLowConfidence
              ? 'bg-yellow-50 text-yellow-800 border border-yellow-200'
              : 'bg-white text-gray-800 border border-gray-200'
      }`}>
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {formattedContent}
        </div>
        
        {/* Timestamp */}
        {showTimestamp && (
          <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
            <Clock className="w-3 h-3" />
            <span>{formatTimestamp(message.timestamp)}</span>
          </div>
        )}
        
        {/* Message Metadata */}
        {showMetadata && message.metadata && (
          <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-500 space-y-1">
            <div className="flex items-center justify-between">
              {message.metadata.confidence && (
                <span className={`${
                  message.metadata.confidence < 0.5 ? 'text-yellow-600' : 'text-green-600'
                }`}>
                  {formatConfidenceScore(message.metadata.confidence)}
                </span>
              )}
              {message.metadata.mode && (
                <span className="capitalize bg-gray-100 px-2 py-1 rounded text-xs">
                  {message.metadata.mode}
                </span>
              )}
            </div>
            
            {message.metadata.processingTime && (
              <div className="text-xs text-gray-400">
                Processed in {message.metadata.processingTime}ms
              </div>
            )}
            
            {hasError && (
              <div className="text-xs text-red-600 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                <span>Message failed to process</span>
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Avatar for User messages */}
      {isUser && (
        <div className="user-avatar w-8 h-8 text-sm flex-shrink-0">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  )
}

export default MessageBubble