import { EnhancedChatMessage, ConversationContext } from '../../types/enhanced-orchestrator'

export interface PersistedConversation {
  sessionId: string
  userId: string
  messages: EnhancedChatMessage[]
  context: ConversationContext | null
  timestamp: string
  metadata: {
    messageCount: number
    lastActivity: string
    conversationMode: 'guided' | 'expert' | 'mixed'
    hasPackages: boolean
  }
}

export interface ConversationPersistenceOptions {
  maxConversations?: number
  maxAge?: number // in milliseconds
  storageKey?: string
}

/**
 * Service for persisting conversation history to localStorage
 */
export class ConversationPersistence {
  private options: Required<ConversationPersistenceOptions>

  constructor(options: ConversationPersistenceOptions = {}) {
    this.options = {
      maxConversations: options.maxConversations || 10,
      maxAge: options.maxAge || 7 * 24 * 60 * 60 * 1000, // 7 days
      storageKey: options.storageKey || 'sparky_conversations'
    }
  }

  /**
   * Save conversation to localStorage
   */
  saveConversation(
    sessionId: string,
    userId: string,
    messages: EnhancedChatMessage[],
    context: ConversationContext | null = null
  ): void {
    try {
      const conversations = this.getAllConversations()
      
      const conversationMode = this.detectConversationMode(messages)
      const hasPackages = messages.some(msg => 
        msg.metadata?.packages && msg.metadata.packages.length > 0
      )

      const persistedConversation: PersistedConversation = {
        sessionId,
        userId,
        messages,
        context,
        timestamp: new Date().toISOString(),
        metadata: {
          messageCount: messages.length,
          lastActivity: new Date().toISOString(),
          conversationMode,
          hasPackages
        }
      }

      // Remove existing conversation with same sessionId
      const filteredConversations = conversations.filter(
        conv => conv.sessionId !== sessionId
      )

      // Add new conversation at the beginning
      filteredConversations.unshift(persistedConversation)

      // Keep only the most recent conversations
      const trimmedConversations = filteredConversations.slice(0, this.options.maxConversations)

      // Save to localStorage
      localStorage.setItem(this.options.storageKey, JSON.stringify(trimmedConversations))
    } catch (error) {
      console.error('Failed to save conversation:', error)
    }
  }

  /**
   * Load conversation from localStorage
   */
  loadConversation(sessionId: string): PersistedConversation | null {
    try {
      const conversations = this.getAllConversations()
      return conversations.find(conv => conv.sessionId === sessionId) || null
    } catch (error) {
      console.error('Failed to load conversation:', error)
      return null
    }
  }

  /**
   * Get all persisted conversations
   */
  getAllConversations(): PersistedConversation[] {
    try {
      const stored = localStorage.getItem(this.options.storageKey)
      if (!stored) return []

      const conversations: PersistedConversation[] = JSON.parse(stored)
      
      // Filter out expired conversations
      const now = Date.now()
      return conversations.filter(conv => {
        const age = now - new Date(conv.timestamp).getTime()
        return age < this.options.maxAge
      })
    } catch (error) {
      console.error('Failed to load conversations:', error)
      return []
    }
  }

  /**
   * Delete a specific conversation
   */
  deleteConversation(sessionId: string): void {
    try {
      const conversations = this.getAllConversations()
      const filteredConversations = conversations.filter(
        conv => conv.sessionId !== sessionId
      )
      localStorage.setItem(this.options.storageKey, JSON.stringify(filteredConversations))
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  /**
   * Clear all conversations
   */
  clearAllConversations(): void {
    try {
      localStorage.removeItem(this.options.storageKey)
    } catch (error) {
      console.error('Failed to clear conversations:', error)
    }
  }

  /**
   * Get conversation summary for display
   */
  getConversationSummary(sessionId: string): {
    messageCount: number
    lastActivity: string
    preview: string
    mode: 'guided' | 'expert' | 'mixed'
  } | null {
    const conversation = this.loadConversation(sessionId)
    if (!conversation) return null

    const lastUserMessage = conversation.messages
      .filter(msg => msg.sender === 'user')
      .pop()

    const preview = lastUserMessage?.content.substring(0, 50) + 
      ((lastUserMessage?.content.length || 0) > 50 ? '...' : '') || 'No messages'

    return {
      messageCount: conversation.metadata.messageCount,
      lastActivity: conversation.metadata.lastActivity,
      preview,
      mode: conversation.metadata.conversationMode
    }
  }

  /**
   * Search conversations by content
   */
  searchConversations(query: string): PersistedConversation[] {
    const conversations = this.getAllConversations()
    const lowerQuery = query.toLowerCase()

    return conversations.filter(conv => 
      conv.messages.some(msg => 
        msg.content.toLowerCase().includes(lowerQuery)
      )
    )
  }

  /**
   * Get storage usage information
   */
  getStorageInfo(): {
    conversationCount: number
    totalSize: number
    oldestConversation: string | null
    newestConversation: string | null
  } {
    const conversations = this.getAllConversations()
    const stored = localStorage.getItem(this.options.storageKey) || ''
    
    return {
      conversationCount: conversations.length,
      totalSize: new Blob([stored]).size,
      oldestConversation: conversations.length > 0 
        ? conversations[conversations.length - 1]?.timestamp || null
        : null,
      newestConversation: conversations.length > 0 
        ? conversations[0]?.timestamp || null
        : null
    }
  }

  /**
   * Detect conversation mode from messages
   */
  private detectConversationMode(messages: EnhancedChatMessage[]): 'guided' | 'expert' | 'mixed' {
    const modes = messages
      .map(msg => msg.metadata?.mode)
      .filter(Boolean) as ('guided' | 'expert')[]

    if (modes.length === 0) return 'expert'

    const guidedCount = modes.filter(mode => mode === 'guided').length
    const expertCount = modes.filter(mode => mode === 'expert').length

    if (guidedCount > expertCount) return 'guided'
    if (expertCount > guidedCount) return 'expert'
    return 'mixed'
  }

  /**
   * Export conversations for backup
   */
  exportConversations(): string {
    const conversations = this.getAllConversations()
    return JSON.stringify(conversations, null, 2)
  }

  /**
   * Import conversations from backup
   */
  importConversations(data: string): boolean {
    try {
      const conversations: PersistedConversation[] = JSON.parse(data)
      
      // Validate the data structure
      if (!Array.isArray(conversations)) {
        throw new Error('Invalid data format')
      }

      // Merge with existing conversations
      const existing = this.getAllConversations()
      const merged = [...conversations, ...existing]
      
      // Remove duplicates by sessionId
      const unique = merged.filter((conv, index, arr) => 
        arr.findIndex(c => c.sessionId === conv.sessionId) === index
      )

      // Keep only the most recent conversations
      const trimmed = unique
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, this.options.maxConversations)

      localStorage.setItem(this.options.storageKey, JSON.stringify(trimmed))
      return true
    } catch (error) {
      console.error('Failed to import conversations:', error)
      return false
    }
  }
}

export default ConversationPersistence