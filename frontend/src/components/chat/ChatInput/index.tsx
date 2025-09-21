import React, { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  disabled?: boolean
  placeholder?: string
  className?: string
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled = false,
  placeholder = 'Type your message...',
  className = ''
}) => {
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`
    }
  }, [message])

  const handleSend = async () => {
    if (!message.trim() || disabled || isLoading) return

    const currentMessage = message.trim()
    setMessage('')
    setIsLoading(true)

    try {
      await onSendMessage(currentMessage)
    } catch (error) {
      console.error('Failed to send message:', error)
      // Restore message on error
      setMessage(currentMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const canSend = message.trim() && !disabled && !isLoading

  return (
    <div className={`flex items-end gap-2 ${className}`}>
      <div className="flex-1 relative">
        <textarea
          ref={inputRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          className="w-full px-4 py-2 pr-12 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-sparky-gold focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed min-h-[40px] max-h-32"
          style={{ 
            scrollbarWidth: 'thin',
            scrollbarColor: '#d1d5db transparent'
          }}
        />
        
        {/* Character count for long messages */}
        {message.length > 200 && (
          <div className="absolute -top-6 right-0 text-xs text-gray-400">
            {message.length}/1000
          </div>
        )}
      </div>
      
      <button
        onClick={handleSend}
        disabled={!canSend}
        className="flex items-center justify-center w-10 h-10 bg-sparky-gold text-black rounded-lg hover:bg-yellow-500 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors duration-200"
        title="Send message"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Send className="w-4 h-4" />
        )}
      </button>
    </div>
  )
}

export default ChatInput