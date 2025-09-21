import React, { useRef, useEffect, useState } from 'react'
import { Zap, RotateCcw, Activity, Save, History, Globe } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { MessageList } from '../MessageList'
import { ChatInput } from '../ChatInput'
import { TypingIndicator } from '../TypingIndicator'
import { ConversationReset, ResetSuccessNotification } from '../ConversationReset'
import { LanguageSelector } from '../../common/LanguageSelector'
import { useEnhancedConversation } from '@hooks/useEnhancedConversation'
import { useLanguage } from '@hooks/useLanguage'
import { EnhancedChatMessage } from '../../../types/enhanced-orchestrator'
import { 
  getModeDisplayText, 
  shouldShowTypingIndicator,
  generateConversationSummary 
} from '../../../utils/messageFormatting'
import { ConversationPersistence, MessageRetryService } from '../../../services/conversation'
import { SelectedItemsPanel } from '../../packages'

interface SparkyChatProps {
  sessionId?: string
  onPackageRecommendation?: (packages: any[]) => void
  onConversationModeChange?: (mode: 'guided' | 'expert') => void
  className?: string
}

export const SparkyChat: React.FC<SparkyChatProps> = ({
  sessionId: _propSessionId,
  onPackageRecommendation,
  onConversationModeChange,
  className = ''
}) => {
  const { t } = useTranslation(['sparky', 'common'])
  const { currentLanguage } = useLanguage()
  
  const {
    messages,
    packages,
    isLoading,
    isTyping,
    canSendMessage,
    conversationMode,
    currentFlowState,
    workflowStatus,
    sessionId: currentSessionId,
    sendMessage,
    addCustomMessage,
    resetConversation,
    hasActiveSession,
    isProcessing
  } = useEnhancedConversation()

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [showMetadata, setShowMetadata] = useState(false)
  const [showResetSuccess, setShowResetSuccess] = useState(false)
  const [showConversationHistory, setShowConversationHistory] = useState(false)
  
  // Services
  const [persistenceService] = useState(() => new ConversationPersistence({
    maxConversations: 10,
    maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
  }))
  
  const [retryService] = useState(() => new MessageRetryService({
    maxRetries: 3,
    retryDelay: 1000,
    backoffMultiplier: 2
  }))

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Initialize with welcome message if no messages exist
  // Fixed 2025-01-09: Prevent duplicate welcome messages and use proper i18n
  // Fixed 2025-01-09: Improved duplicate prevention logic
  useEffect(() => {
    const hasWelcomeMessage = messages.some(msg => msg.id?.startsWith('welcome-'))
    if (messages.length === 0 && !hasWelcomeMessage) {
      // Only add welcome message if no messages exist AND no welcome message already exists
      // Fixed 2025-01-09: Use localized welcome message instead of hardcoded English
      // Fixed 2025-01-09: Use timestamp-based unique ID to prevent React key conflicts
      const welcomeMessage: EnhancedChatMessage = {
        id: `welcome-${Date.now()}`,
        content: t('sparky:welcome') + '\n\n' + t('sparky:placeholder'),
        sender: 'sparky',
        timestamp: new Date().toISOString(),
        metadata: {
          confidence: 1.0,
          mode: 'expert'
        }
      }
      addCustomMessage(welcomeMessage)
    }
  }, [messages.length, addCustomMessage, t])

  // Notify parent components of package recommendations
  useEffect(() => {
    if (packages.length > 0 && onPackageRecommendation) {
      onPackageRecommendation(packages)
    }
  }, [packages, onPackageRecommendation])

  // Notify parent of conversation mode changes
  useEffect(() => {
    if (conversationMode && conversationMode !== 'unknown' && onConversationModeChange) {
      onConversationModeChange(conversationMode as 'guided' | 'expert')
    }
  }, [conversationMode, onConversationModeChange])

  // Auto-save conversation to localStorage
  useEffect(() => {
    if (messages.length > 0 && currentSessionId) {
      persistenceService.saveConversation(
        currentSessionId,
        'current-user', // TODO: Get from auth context
        messages
      )
    }
  }, [messages, currentSessionId, persistenceService])

  const handleSendMessage = async (message: string) => {
    try {
      await sendMessage(message, {
        flowType: conversationMode === 'guided' ? 'guided_flow' : 'quick_package',
        language: currentLanguage,
        enableObservability: true
      })
    } catch (error: any) {
      console.error('Chat error:', error)
      
      // Register for retry if it's a retryable error
      const lastMessage = messages[messages.length - 1]
      if (lastMessage && lastMessage.sender === 'user') {
        const registered = retryService.registerForRetry(
          lastMessage,
          error.message || 'unknown_error',
          async (retryMessage) => {
            await sendMessage(retryMessage.content, {
              flowType: conversationMode === 'guided' ? 'guided_flow' : 'quick_package',
              language: currentLanguage,
              enableObservability: true
            })
          }
        )
        
        if (registered) {
          console.log('Message registered for retry')
        }
      }
    }
  }

  const handleResetConversation = async () => {
    // Clear retry service
    retryService.clearAllRetryInfo()
    
    // Reset conversation
    resetConversation()
    
    // Show success notification
    setShowResetSuccess(true)
  }



  const handleLoadConversation = (sessionId: string) => {
    const conversation = persistenceService.loadConversation(sessionId)
    if (conversation) {
      // TODO: Load conversation into Redux state
      console.log('Loading conversation:', conversation)
    }
  }

  const conversationSummary = generateConversationSummary(messages)
  const showTyping = shouldShowTypingIndicator(messages, isTyping)
  const retryableMessages = retryService.getAllRetryableMessages()
  const conversationHistory = persistenceService.getAllConversations()


  return (
    <div className={`flex h-full ${className}`}>
      {/* Chat Section */}
      <div className="flex flex-col flex-1">
        {/* Chat Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/20">
          <div className="flex items-center gap-3">
            <div className="sparky-avatar w-10 h-10 text-base">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-semibold text-white">{t('sparky:title')}</h2>
              <p className="text-sm text-white/70">
                {t('sparky:subtitle')}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Workflow Status Indicator */}
            {hasActiveSession && (
              <div className="flex items-center gap-1 text-xs text-white/70">
                <Activity className={`w-3 h-3 ${isProcessing ? 'animate-pulse' : ''}`} />
                <span className="capitalize">{workflowStatus}</span>
                {currentFlowState && (
                  <span className="text-white/50">• {currentFlowState}</span>
                )}
              </div>
            )}
            
            {/* Retry Status */}
            {retryableMessages.length > 0 && (
              <div className="flex items-center gap-1 text-xs text-yellow-300">
                <RotateCcw className="w-3 h-3" />
                <span>{retryableMessages.length} retrying</span>
              </div>
            )}
            
            {/* Language Selector */}
            <div className="relative">
              <LanguageSelector 
                variant="dropdown"
                showFlags={true}
                showNativeNames={false}
                className="text-sm"
              />
            </div>
            
            {/* Conversation History */}
            <button
              onClick={() => setShowConversationHistory(!showConversationHistory)}
              className={`p-2 rounded-lg transition-colors ${
                showConversationHistory 
                  ? 'text-white bg-white/10' 
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
              title={t('sparky:conversation.history')}
            >
              <History className="w-4 h-4" />
            </button>
            
            {/* Auto-save Indicator */}
            {messages.length > 0 && (
              <div className="flex items-center gap-1 text-xs text-green-300">
                <Save className="w-3 h-3" />
                <span>Saved</span>
              </div>
            )}
            
            {/* Reset Button */}
            <ConversationReset
              onReset={handleResetConversation}
              messageCount={messages.length}
              hasPackages={packages.length > 0}
              className="p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            />
            
            {/* Metadata Toggle */}
            <button
              onClick={() => setShowMetadata(!showMetadata)}
              className={`p-2 rounded-lg transition-colors ${
                showMetadata 
                  ? 'text-white bg-white/10' 
                  : 'text-white/70 hover:text-white hover:bg-white/10'
              }`}
              title="Toggle message metadata"
            >
              <Activity className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Conversation Summary (when metadata is shown) */}
        {/* Conversation Summary Temporarily Disabled */}

        {/* Conversation History Panel */}
        {showConversationHistory && (
          <div className="px-4 py-2 bg-white/5 border-b border-white/10 max-h-32 overflow-y-auto">
            <div className="text-xs text-white/70 mb-2">Recent Conversations</div>
            {conversationHistory.length === 0 ? (
              <div className="text-xs text-white/50">No saved conversations</div>
            ) : (
              <div className="space-y-1">
                {conversationHistory.slice(0, 5).map((conv) => {
                  const summary = persistenceService.getConversationSummary(conv.sessionId)
                  return summary ? (
                    <button
                      key={conv.sessionId}
                      onClick={() => handleLoadConversation(conv.sessionId)}
                      className="w-full text-left p-2 text-xs bg-white/5 hover:bg-white/10 rounded transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="truncate">{summary.preview}</span>
                        <span className="text-white/50 ml-2">{summary.messageCount}msg</span>
                      </div>
                    </button>
                  ) : null
                })}
              </div>
            )}
          </div>
        )}

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
          <MessageList 
            messages={messages}
            showTimestamp={showMetadata}
            showMetadata={showMetadata}
          />
          
          {showTyping && (
            <TypingIndicator 
              message={currentFlowState ? `Processing ${currentFlowState}...` : 'Sparky is thinking...'}
            />
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <div className="border-t border-white/20 p-4">
          <ChatInput
            onSendMessage={handleSendMessage}
            disabled={!canSendMessage || isLoading}
            placeholder={
              conversationMode === 'guided' 
                ? "Tell me about your welding needs..." 
                : "Ask Sparky about welding equipment..."
            }
          />
        </div>

        {/* Reset Success Notification */}
        {showResetSuccess && (
          <ResetSuccessNotification
            onDismiss={() => setShowResetSuccess(false)}
            autoHide={true}
            hideDelay={3000}
          />
        )}
      </div>
      
      {/* Selected Items Panel */}
      <SelectedItemsPanel 
        packages={packages}
        className="flex-shrink-0"
      />
    </div>
  )
}

export default SparkyChat