import { EnhancedChatMessage } from '../../types/enhanced-orchestrator'

export interface RetryOptions {
  maxRetries?: number
  retryDelay?: number
  backoffMultiplier?: number
  retryableErrors?: string[]
}

export interface RetryAttempt {
  attemptNumber: number
  timestamp: string
  error: string
  nextRetryAt?: string
}

export interface RetryableMessage {
  originalMessage: EnhancedChatMessage
  retryAttempts: RetryAttempt[]
  lastAttempt: string
  nextRetryAt: string | null
  isRetrying: boolean
  canRetry: boolean
}

/**
 * Service for handling message retry and error recovery
 */
export class MessageRetryService {
  private options: Required<RetryOptions>
  private retryableMessages: Map<string, RetryableMessage> = new Map()
  private retryTimeouts: Map<string, NodeJS.Timeout> = new Map()

  constructor(options: RetryOptions = {}) {
    this.options = {
      maxRetries: options.maxRetries || 3,
      retryDelay: options.retryDelay || 1000, // 1 second
      backoffMultiplier: options.backoffMultiplier || 2,
      retryableErrors: options.retryableErrors || [
        'network_error',
        'timeout_error',
        'server_error',
        'rate_limit_error'
      ]
    }
  }

  /**
   * Register a message for retry
   */
  registerForRetry(
    message: EnhancedChatMessage,
    error: string,
    onRetry: (message: EnhancedChatMessage) => Promise<void>
  ): boolean {
    if (!this.isRetryableError(error)) {
      return false
    }

    const existing = this.retryableMessages.get(message.id)
    const attemptNumber = existing ? existing.retryAttempts.length + 1 : 1

    if (attemptNumber > this.options.maxRetries) {
      return false
    }

    const delay = this.calculateRetryDelay(attemptNumber)
    const nextRetryAt = new Date(Date.now() + delay).toISOString()

    const retryAttempt: RetryAttempt = {
      attemptNumber,
      timestamp: new Date().toISOString(),
      error,
      nextRetryAt
    }

    const retryableMessage: RetryableMessage = {
      originalMessage: message,
      retryAttempts: existing ? [...existing.retryAttempts, retryAttempt] : [retryAttempt],
      lastAttempt: retryAttempt.timestamp,
      nextRetryAt,
      isRetrying: false,
      canRetry: true
    }

    this.retryableMessages.set(message.id, retryableMessage)

    // Schedule retry
    const timeoutId = setTimeout(async () => {
      await this.executeRetry(message.id, onRetry)
    }, delay)

    this.retryTimeouts.set(message.id, timeoutId)

    return true
  }

  /**
   * Manually retry a message
   */
  async manualRetry(
    messageId: string,
    onRetry: (message: EnhancedChatMessage) => Promise<void>
  ): Promise<boolean> {
    const retryableMessage = this.retryableMessages.get(messageId)
    if (!retryableMessage || !retryableMessage.canRetry || retryableMessage.isRetrying) {
      return false
    }

    return await this.executeRetry(messageId, onRetry)
  }

  /**
   * Cancel retry for a message
   */
  cancelRetry(messageId: string): void {
    const timeout = this.retryTimeouts.get(messageId)
    if (timeout) {
      clearTimeout(timeout)
      this.retryTimeouts.delete(messageId)
    }

    const retryableMessage = this.retryableMessages.get(messageId)
    if (retryableMessage) {
      retryableMessage.canRetry = false
      retryableMessage.nextRetryAt = null
    }
  }

  /**
   * Get retry information for a message
   */
  getRetryInfo(messageId: string): RetryableMessage | null {
    return this.retryableMessages.get(messageId) || null
  }

  /**
   * Get all retryable messages
   */
  getAllRetryableMessages(): RetryableMessage[] {
    return Array.from(this.retryableMessages.values())
  }

  /**
   * Clear retry information for a message
   */
  clearRetryInfo(messageId: string): void {
    this.cancelRetry(messageId)
    this.retryableMessages.delete(messageId)
  }

  /**
   * Clear all retry information
   */
  clearAllRetryInfo(): void {
    // Cancel all timeouts
    this.retryTimeouts.forEach(timeout => clearTimeout(timeout))
    this.retryTimeouts.clear()
    this.retryableMessages.clear()
  }

  /**
   * Check if an error is retryable
   */
  private isRetryableError(error: string): boolean {
    return this.options.retryableErrors.includes(error.toLowerCase())
  }

  /**
   * Calculate retry delay with exponential backoff
   */
  private calculateRetryDelay(attemptNumber: number): number {
    return this.options.retryDelay * Math.pow(this.options.backoffMultiplier, attemptNumber - 1)
  }

  /**
   * Execute retry for a message
   */
  private async executeRetry(
    messageId: string,
    onRetry: (message: EnhancedChatMessage) => Promise<void>
  ): Promise<boolean> {
    const retryableMessage = this.retryableMessages.get(messageId)
    if (!retryableMessage || !retryableMessage.canRetry) {
      return false
    }

    retryableMessage.isRetrying = true
    this.retryTimeouts.delete(messageId)

    try {
      await onRetry(retryableMessage.originalMessage)
      
      // Success - clear retry info
      this.clearRetryInfo(messageId)
      return true
    } catch (error: any) {
      retryableMessage.isRetrying = false
      
      // Check if we should retry again
      const nextAttemptNumber = retryableMessage.retryAttempts.length + 1
      if (nextAttemptNumber <= this.options.maxRetries && this.isRetryableError(error.message)) {
        // Register for another retry
        const delay = this.calculateRetryDelay(nextAttemptNumber)
        const nextRetryAt = new Date(Date.now() + delay).toISOString()

        const retryAttempt: RetryAttempt = {
          attemptNumber: nextAttemptNumber,
          timestamp: new Date().toISOString(),
          error: error.message,
          nextRetryAt
        }

        retryableMessage.retryAttempts.push(retryAttempt)
        retryableMessage.lastAttempt = retryAttempt.timestamp
        retryableMessage.nextRetryAt = nextRetryAt

        // Schedule next retry
        const timeoutId = setTimeout(async () => {
          await this.executeRetry(messageId, onRetry)
        }, delay)

        this.retryTimeouts.set(messageId, timeoutId)
      } else {
        // Max retries reached or non-retryable error
        retryableMessage.canRetry = false
        retryableMessage.nextRetryAt = null
      }

      return false
    }
  }

  /**
   * Get retry statistics
   */
  getRetryStatistics(): {
    totalRetryableMessages: number
    activeRetries: number
    completedRetries: number
    failedRetries: number
    averageRetryAttempts: number
  } {
    const messages = Array.from(this.retryableMessages.values())
    
    const activeRetries = messages.filter(msg => msg.canRetry && msg.nextRetryAt).length
    const completedRetries = messages.filter(msg => !msg.canRetry && msg.retryAttempts.length > 0).length
    const failedRetries = messages.filter(msg => !msg.canRetry && msg.retryAttempts.length >= this.options.maxRetries).length
    
    const totalAttempts = messages.reduce((sum, msg) => sum + msg.retryAttempts.length, 0)
    const averageRetryAttempts = messages.length > 0 ? totalAttempts / messages.length : 0

    return {
      totalRetryableMessages: messages.length,
      activeRetries,
      completedRetries,
      failedRetries,
      averageRetryAttempts
    }
  }

  /**
   * Create error recovery suggestions
   */
  getErrorRecoverySuggestions(error: string): string[] {
    const suggestions: string[] = []

    switch (error.toLowerCase()) {
      case 'network_error':
        suggestions.push('Check your internet connection')
        suggestions.push('Try refreshing the page')
        suggestions.push('Wait a moment and try again')
        break
      
      case 'timeout_error':
        suggestions.push('The request took too long to process')
        suggestions.push('Try simplifying your request')
        suggestions.push('Check your connection speed')
        break
      
      case 'server_error':
        suggestions.push('The server encountered an error')
        suggestions.push('Try again in a few minutes')
        suggestions.push('Contact support if the problem persists')
        break
      
      case 'rate_limit_error':
        suggestions.push('You\'re sending messages too quickly')
        suggestions.push('Wait a moment before trying again')
        suggestions.push('Consider breaking complex requests into smaller parts')
        break
      
      default:
        suggestions.push('An unexpected error occurred')
        suggestions.push('Try refreshing the page')
        suggestions.push('Contact support if the problem continues')
    }

    return suggestions
  }
}

export default MessageRetryService