import { EnhancedChatMessage } from '../types/enhanced-orchestrator'

/**
 * Utility functions for message formatting and display logic
 */

export interface MessageDisplayOptions {
  showTimestamp?: boolean
  showMetadata?: boolean
  showConfidence?: boolean
  maxLength?: number
}

/**
 * Format message content for display
 */
export const formatMessageContent = (
  message: EnhancedChatMessage,
  options: MessageDisplayOptions = {}
): string => {
  let content = message.content

  // Truncate if max length specified
  if (options.maxLength && content.length > options.maxLength) {
    content = content.substring(0, options.maxLength) + '...'
  }

  return content
}

/**
 * Format timestamp for display
 */
export const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  
  return date.toLocaleDateString()
}

/**
 * Get message display class based on sender and metadata
 */
export const getMessageDisplayClass = (message: EnhancedChatMessage): string => {
  const baseClass = 'message-bubble'
  const senderClass = message.sender === 'user' ? 'user-message' : 'sparky-message'
  
  let statusClass = ''
  if (message.metadata?.error) {
    statusClass = 'error-message'
  } else if (message.metadata?.confidence && message.metadata.confidence < 0.5) {
    statusClass = 'low-confidence-message'
  }

  return [baseClass, senderClass, statusClass].filter(Boolean).join(' ')
}

/**
 * Extract conversation mode from message history
 */
export const detectConversationModeFromHistory = (
  messages: EnhancedChatMessage[]
): 'guided' | 'expert' | 'mixed' => {
  const recentMessages = messages.slice(-5) // Look at last 5 messages
  const modes = recentMessages
    .map(msg => msg.metadata?.mode)
    .filter(Boolean) as ('guided' | 'expert')[]

  if (modes.length === 0) return 'expert' // Default

  const guidedCount = modes.filter(mode => mode === 'guided').length
  const expertCount = modes.filter(mode => mode === 'expert').length

  if (guidedCount > expertCount) return 'guided'
  if (expertCount > guidedCount) return 'expert'
  return 'mixed'
}

/**
 * Generate conversation summary
 */
export const generateConversationSummary = (
  messages: EnhancedChatMessage[]
): {
  messageCount: number
  userMessages: number
  sparkyMessages: number
  averageConfidence: number
  dominantMode: 'guided' | 'expert' | 'mixed'
  hasErrors: boolean
} => {
  const userMessages = messages.filter(msg => msg.sender === 'user')
  const sparkyMessages = messages.filter(msg => msg.sender === 'sparky')
  
  const confidenceScores = sparkyMessages
    .map(msg => msg.metadata?.confidence)
    .filter(score => typeof score === 'number') as number[]
  
  const averageConfidence = confidenceScores.length > 0
    ? confidenceScores.reduce((sum, score) => sum + score, 0) / confidenceScores.length
    : 0

  const hasErrors = messages.some(msg => msg.metadata?.error)
  const dominantMode = detectConversationModeFromHistory(messages)

  return {
    messageCount: messages.length,
    userMessages: userMessages.length,
    sparkyMessages: sparkyMessages.length,
    averageConfidence,
    dominantMode,
    hasErrors
  }
}

/**
 * Format confidence score for display
 */
export const formatConfidenceScore = (confidence: number): string => {
  const percentage = Math.round(confidence * 100)
  
  if (percentage >= 90) return `${percentage}% (Excellent)`
  if (percentage >= 75) return `${percentage}% (Good)`
  if (percentage >= 60) return `${percentage}% (Fair)`
  return `${percentage}% (Low)`
}

/**
 * Get conversation mode display text
 */
export const getModeDisplayText = (mode: 'guided' | 'expert' | 'mixed' | 'unknown'): string => {
  const modeTexts = {
    guided: 'Guided Mode - Step-by-step assistance',
    expert: 'Expert Mode - Direct recommendations',
    mixed: 'Mixed Mode - Adaptive assistance',
    unknown: 'Detecting mode...'
  }

  return modeTexts[mode] || 'Unknown mode'
}

/**
 * Check if message should show typing indicator
 */
export const shouldShowTypingIndicator = (
  messages: EnhancedChatMessage[],
  isTyping: boolean
): boolean => {
  if (!isTyping) return false
  
  const lastMessage = messages[messages.length - 1]
  return !lastMessage || lastMessage.sender === 'user'
}

/**
 * Format package count message
 */
export const formatPackageCountMessage = (count: number): string => {
  if (count === 0) return 'No packages found matching your requirements.'
  if (count === 1) return 'I found 1 welding package that matches your requirements.'
  return `I found ${count} welding packages that match your requirements.`
}

/**
 * Extract action items from message content
 */
export const extractActionItems = (content: string): string[] => {
  const actionPatterns = [
    /please (.*?)(?:\.|$)/gi,
    /you should (.*?)(?:\.|$)/gi,
    /try (.*?)(?:\.|$)/gi,
    /consider (.*?)(?:\.|$)/gi
  ]

  const actions: string[] = []
  
  actionPatterns.forEach(pattern => {
    const matches = content.match(pattern)
    if (matches) {
      matches.forEach(match => {
        const action = match.replace(/^(please|you should|try|consider)\s*/i, '').replace(/\.$/, '')
        if (action.length > 5) { // Filter out very short matches
          actions.push(action.charAt(0).toUpperCase() + action.slice(1))
        }
      })
    }
  })

  return [...new Set(actions)] // Remove duplicates
}

export default {
  formatMessageContent,
  formatTimestamp,
  getMessageDisplayClass,
  detectConversationModeFromHistory,
  generateConversationSummary,
  formatConfidenceScore,
  getModeDisplayText,
  shouldShowTypingIndicator,
  formatPackageCountMessage,
  extractActionItems
}