import React from 'react'
import { MessageBubble } from '../MessageBubble'
import { EnhancedChatMessage } from '../../../types/enhanced-orchestrator'

interface MessageListProps {
  messages: EnhancedChatMessage[]
  className?: string
  showTimestamp?: boolean
  showMetadata?: boolean
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  className = '',
  showTimestamp = false,
  showMetadata = true
}) => {
  return (
    <div className={`space-y-4 ${className}`}>
      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          showTimestamp={showTimestamp}
          showMetadata={showMetadata}
        />
      ))}
    </div>
  )
}

export default MessageList