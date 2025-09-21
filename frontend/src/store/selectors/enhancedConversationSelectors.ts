import { createSelector } from '@reduxjs/toolkit'
import { RootState } from '../index'
// import { EnhancedWeldingPackage, EnhancedChatMessage } from '../../types/enhanced-orchestrator'

// Base selectors
const selectEnhancedConversationState = (state: RootState) => state.enhancedConversation

// Session selectors
export const selectSessionId = createSelector(
  [selectEnhancedConversationState],
  (state) => state.sessionId
)

export const selectUserId = createSelector(
  [selectEnhancedConversationState],
  (state) => state.userId
)

export const selectCurrentFlowState = createSelector(
  [selectEnhancedConversationState],
  (state) => state.currentFlowState
)

export const selectWorkflowStatus = createSelector(
  [selectEnhancedConversationState],
  (state) => state.workflowStatus
)

// Message selectors
export const selectMessages = createSelector(
  [selectEnhancedConversationState],
  (state) => state.messages
)

export const selectLastMessage = createSelector(
  [selectMessages],
  (messages) => messages[messages.length - 1] || null
)

export const selectMessageCount = createSelector(
  [selectMessages],
  (messages) => messages.length
)

export const selectUserMessages = createSelector(
  [selectMessages],
  (messages) => messages.filter(msg => msg.sender === 'user')
)

export const selectSparkyMessages = createSelector(
  [selectMessages],
  (messages) => messages.filter(msg => msg.sender === 'sparky')
)

export const selectRecentMessages = createSelector(
  [selectMessages],
  (messages) => messages.slice(-10) // Last 10 messages
)

// Package selectors
export const selectPackages = createSelector(
  [selectEnhancedConversationState],
  (state) => state.packages
)

export const selectSelectedPackage = createSelector(
  [selectEnhancedConversationState],
  (state) => state.selectedPackage
)

export const selectPackageCount = createSelector(
  [selectPackages],
  (packages) => packages.length
)

export const selectPackageById = createSelector(
  [selectPackages, (_, packageId: string) => packageId],
  (packages, packageId) => packages.find(pkg => pkg.package_id === packageId) || null
)

export const selectTopPackages = createSelector(
  [selectPackages],
  (packages) => packages
    .slice()
    .sort((a, b) => b.compatibility_confidence - a.compatibility_confidence)
    .slice(0, 3)
)

export const selectPackagesByCompatibility = createSelector(
  [selectPackages],
  (packages) => packages
    .slice()
    .sort((a, b) => b.compatibility_confidence - a.compatibility_confidence)
)

// Performance and metrics selectors
export const selectProcessingTimeMs = createSelector(
  [selectEnhancedConversationState],
  (state) => state.processingTimeMs
)

export const selectValidationScore = createSelector(
  [selectEnhancedConversationState],
  (state) => state.validationScore
)

export const selectRecommendationConfidence = createSelector(
  [selectEnhancedConversationState],
  (state) => state.recommendationConfidence
)

export const selectCompatibilityConfidence = createSelector(
  [selectEnhancedConversationState],
  (state) => state.compatibilityConfidence
)

export const selectPerformanceMetrics = createSelector(
  [selectEnhancedConversationState],
  (state) => ({
    processingTimeMs: state.processingTimeMs,
    validationScore: state.validationScore,
    recommendationConfidence: state.recommendationConfidence,
    compatibilityConfidence: state.compatibilityConfidence,
    cacheHitRate: state.cacheHitRate
  })
)

// Agent selectors
export const selectAgentDecisions = createSelector(
  [selectEnhancedConversationState],
  (state) => state.agentDecisions
)

export const selectCurrentAgent = createSelector(
  [selectEnhancedConversationState],
  (state) => state.currentAgent
)

export const selectEnhancedFeatures = createSelector(
  [selectEnhancedConversationState],
  (state) => state.enhancedFeatures
)

export const selectRecentAgentDecisions = createSelector(
  [selectAgentDecisions],
  (decisions) => decisions.slice(-5) // Last 5 decisions
)

export const selectAgentDecisionsByRole = createSelector(
  [selectAgentDecisions, (_, role: string) => role],
  (decisions, role) => decisions.filter(decision => decision.agent_role === role)
)

// UI state selectors
export const selectIsLoading = createSelector(
  [selectEnhancedConversationState],
  (state) => state.isLoading
)

export const selectIsTyping = createSelector(
  [selectEnhancedConversationState],
  (state) => state.isTyping
)

export const selectError = createSelector(
  [selectEnhancedConversationState],
  (state) => state.error
)

export const selectWarnings = createSelector(
  [selectEnhancedConversationState],
  (state) => state.warnings
)

export const selectHasError = createSelector(
  [selectError],
  (error) => error !== null
)

export const selectHasWarnings = createSelector(
  [selectWarnings],
  (warnings) => warnings.length > 0
)

// Conversation mode selectors
export const selectConversationMode = createSelector(
  [selectEnhancedConversationState],
  (state) => state.conversationMode
)

export const selectIsGuidedFlow = createSelector(
  [selectEnhancedConversationState],
  (state) => state.isGuidedFlow
)

export const selectIsExpertMode = createSelector(
  [selectConversationMode],
  (mode) => mode === 'expert'
)

export const selectIsGuidedMode = createSelector(
  [selectConversationMode],
  (mode) => mode === 'guided'
)

// Activity selectors
export const selectLastActivity = createSelector(
  [selectEnhancedConversationState],
  (state) => state.lastActivity
)

export const selectIsActive = createSelector(
  [selectLastActivity],
  (lastActivity) => {
    if (!lastActivity) return false
    const lastActivityTime = new Date(lastActivity).getTime()
    const now = new Date().getTime()
    const fiveMinutesAgo = now - (5 * 60 * 1000)
    return lastActivityTime > fiveMinutesAgo
  }
)

// Complex selectors
export const selectConversationSummary = createSelector(
  [
    selectSessionId,
    selectMessageCount,
    selectPackageCount,
    selectConversationMode,
    selectWorkflowStatus,
    selectProcessingTimeMs
  ],
  (sessionId, messageCount, packageCount, mode, status, processingTime) => ({
    sessionId,
    messageCount,
    packageCount,
    conversationMode: mode,
    workflowStatus: status,
    processingTimeMs: processingTime,
    hasSession: sessionId !== null,
    hasPackages: packageCount > 0,
    isActive: status === 'processing'
  })
)

export const selectConversationContext = createSelector(
  [
    selectSessionId,
    selectUserId,
    selectCurrentFlowState,
    selectWorkflowStatus,
    selectRecentMessages,
    selectConversationMode
  ],
  (sessionId, userId, flowState, workflowStatus) => ({
    sessionId: sessionId || '',
    userId,
    currentFlowState: flowState,
    workflowStatus,
    packages: [], // Will be filled by component
    processingTimeMs: 0, // Will be filled by component
    validationScore: 0, // Will be filled by component
    recommendationConfidence: 0, // Will be filled by component
    compatibilityConfidence: 0, // Will be filled by component
    agentDecisions: [], // Will be filled by component
    currentAgent: null, // Will be filled by component
    enhancedFeatures: {
      flowManagerUsed: false,
      errorHandlerUsed: false,
      hierarchicalState: false,
      observabilityEnabled: true
    }
  })
)

export const selectCanSendMessage = createSelector(
  [selectIsLoading, selectIsTyping, selectWorkflowStatus],
  (isLoading, isTyping, workflowStatus) => 
    !isLoading && !isTyping && workflowStatus !== 'processing'
)

export const selectShouldShowPackages = createSelector(
  [selectPackages, selectWorkflowStatus, selectConversationMode],
  (packages, workflowStatus, mode) => 
    packages.length > 0 && 
    workflowStatus === 'completed' && 
    (mode === 'expert' || mode === 'guided')
)

export const selectConversationStats = createSelector(
  [
    selectMessageCount,
    selectPackageCount,
    selectAgentDecisions,
    selectProcessingTimeMs,
    selectValidationScore,
    selectRecommendationConfidence
  ],
  (messageCount, packageCount, agentDecisions, processingTime, validationScore, recommendationConfidence) => ({
    totalMessages: messageCount,
    totalPackages: packageCount,
    totalAgentDecisions: agentDecisions.length,
    averageProcessingTime: processingTime,
    averageValidationScore: validationScore,
    averageRecommendationConfidence: recommendationConfidence,
    uniqueAgents: [...new Set(agentDecisions.map(d => d.agent_role))].length
  })
)