import { useCallback } from 'react'
import { useAppDispatch, useAppSelector } from './redux'
import {
  sendEnhancedMessage,
  getWorkflowStatus,
  cancelWorkflow,
  checkServiceHealth,
  setSelectedPackage,
  resetSession,
  clearError,
  clearWarnings,
  setConversationMode,
  addMessage
} from '@store/slices/enhancedConversationSlice'
import {
  selectMessages,
  selectPackages,
  selectSelectedPackage,
  selectIsLoading,
  selectIsTyping,
  selectError,
  selectWarnings,
  selectSessionId,
  selectConversationMode,
  selectWorkflowStatus,
  selectCurrentFlowState,
  selectCanSendMessage,
  selectShouldShowPackages,
  selectConversationSummary,
  selectPerformanceMetrics,
  selectAgentDecisions
} from '@store/selectors/enhancedConversationSelectors'
import { EnhancedWeldingPackage, EnhancedChatMessage } from '../types/enhanced-orchestrator'

/**
 * Custom hook for enhanced conversation management
 * Provides a clean interface for interacting with the enhanced orchestrator
 */
export const useEnhancedConversation = () => {
  const dispatch = useAppDispatch()

  // Selectors
  const messages = useAppSelector(selectMessages)
  const packages = useAppSelector(selectPackages)
  const selectedPackage = useAppSelector(selectSelectedPackage)
  const isLoading = useAppSelector(selectIsLoading)
  const isTyping = useAppSelector(selectIsTyping)
  const error = useAppSelector(selectError)
  const warnings = useAppSelector(selectWarnings)
  const sessionId = useAppSelector(selectSessionId)
  const conversationMode = useAppSelector(selectConversationMode)
  const workflowStatus = useAppSelector(selectWorkflowStatus)
  const currentFlowState = useAppSelector(selectCurrentFlowState)
  const canSendMessage = useAppSelector(selectCanSendMessage)
  const shouldShowPackages = useAppSelector(selectShouldShowPackages)
  const conversationSummary = useAppSelector(selectConversationSummary)
  const performanceMetrics = useAppSelector(selectPerformanceMetrics)
  const agentDecisions = useAppSelector(selectAgentDecisions)

  // Actions
  const sendMessage = useCallback(
    async (
      message: string,
      options?: {
        flowType?: 'quick_package' | 'guided_flow'
        language?: string
        enableObservability?: boolean
      }
    ) => {
      if (!canSendMessage) {
        throw new Error('Cannot send message at this time')
      }

      const result = await dispatch(sendEnhancedMessage({
        message,
        flowType: options?.flowType || 'quick_package',
        language: options?.language || 'en',
        enableObservability: options?.enableObservability ?? true
      }))

      if (sendEnhancedMessage.rejected.match(result)) {
        throw result.payload
      }

      return result.payload
    },
    [dispatch, canSendMessage]
  )

  const selectPackage = useCallback(
    (packageData: EnhancedWeldingPackage | null) => {
      dispatch(setSelectedPackage(packageData))
    },
    [dispatch]
  )

  const resetConversation = useCallback(() => {
    dispatch(resetSession())
  }, [dispatch])

  const clearCurrentError = useCallback(() => {
    dispatch(clearError())
  }, [dispatch])

  const clearCurrentWarnings = useCallback(() => {
    dispatch(clearWarnings())
  }, [dispatch])

  const setMode = useCallback(
    (mode: 'guided' | 'expert' | 'unknown') => {
      dispatch(setConversationMode(mode))
    },
    [dispatch]
  )

  const addCustomMessage = useCallback(
    (message: EnhancedChatMessage) => {
      dispatch(addMessage(message))
    },
    [dispatch]
  )

  const checkWorkflowStatus = useCallback(
    async (sessionId: string) => {
      const result = await dispatch(getWorkflowStatus(sessionId))
      if (getWorkflowStatus.rejected.match(result)) {
        throw result.payload
      }
      return result.payload
    },
    [dispatch]
  )

  const cancelCurrentWorkflow = useCallback(
    async (sessionId: string) => {
      const result = await dispatch(cancelWorkflow(sessionId))
      if (cancelWorkflow.rejected.match(result)) {
        throw result.payload
      }
      return result.payload
    },
    [dispatch]
  )

  const checkHealth = useCallback(async () => {
    const result = await dispatch(checkServiceHealth())
    if (checkServiceHealth.rejected.match(result)) {
      throw result.payload
    }
    return result.payload
  }, [dispatch])

  // Utility functions
  const getPackageById = useCallback(
    (packageId: string): EnhancedWeldingPackage | null => {
      return packages.find(pkg => pkg.package_id === packageId) || null
    },
    [packages]
  )

  const getMessageById = useCallback(
    (messageId: string): EnhancedChatMessage | null => {
      return messages.find(msg => msg.id === messageId) || null
    },
    [messages]
  )

  const getLastUserMessage = useCallback((): EnhancedChatMessage | null => {
    const userMessages = messages.filter(msg => msg.sender === 'user')
    return userMessages[userMessages.length - 1] || null
  }, [messages])

  const getLastSparkyMessage = useCallback((): EnhancedChatMessage | null => {
    const sparkyMessages = messages.filter(msg => msg.sender === 'sparky')
    return sparkyMessages[sparkyMessages.length - 1] || null
  }, [messages])

  const hasActiveSession = useCallback((): boolean => {
    return sessionId !== null && workflowStatus !== 'idle'
  }, [sessionId, workflowStatus])

  const isProcessing = useCallback((): boolean => {
    return workflowStatus === 'processing' || isLoading || isTyping
  }, [workflowStatus, isLoading, isTyping])

  const hasRecommendations = useCallback((): boolean => {
    return packages.length > 0
  }, [packages])

  const getTopRecommendation = useCallback((): EnhancedWeldingPackage | null => {
    if (packages.length === 0) return null
    return packages.reduce((best, current) => 
      current.compatibility_confidence > best.compatibility_confidence ? current : best
    )
  }, [packages])

  return {
    // State
    messages,
    packages,
    selectedPackage,
    isLoading,
    isTyping,
    error,
    warnings,
    sessionId,
    conversationMode,
    workflowStatus,
    currentFlowState,
    conversationSummary,
    performanceMetrics,
    agentDecisions,

    // Computed state
    canSendMessage,
    shouldShowPackages,
    hasActiveSession: hasActiveSession(),
    isProcessing: isProcessing(),
    hasRecommendations: hasRecommendations(),

    // Actions
    sendMessage,
    selectPackage,
    resetConversation,
    clearCurrentError,
    clearCurrentWarnings,
    setMode,
    addCustomMessage,
    checkWorkflowStatus,
    cancelCurrentWorkflow,
    checkHealth,

    // Utilities
    getPackageById,
    getMessageById,
    getLastUserMessage,
    getLastSparkyMessage,
    getTopRecommendation
  }
}

/**
 * Hook for package-specific operations
 */
export const usePackageOperations = () => {
  const dispatch = useAppDispatch()
  const packages = useAppSelector(selectPackages)
  const selectedPackage = useAppSelector(selectSelectedPackage)

  const selectPackage = useCallback(
    (packageData: EnhancedWeldingPackage | null) => {
      dispatch(setSelectedPackage(packageData))
    },
    [dispatch]
  )

  const calculatePackageTotal = useCallback(
    (pkg: EnhancedWeldingPackage): number => {
      if (pkg.total_price) return pkg.total_price

      let total = 0
      if (pkg.powersource?.price) total += pkg.powersource.price
      if (pkg.feeder?.price) total += pkg.feeder.price
      if (pkg.cooler?.price) total += pkg.cooler.price
      if (pkg.torch?.price) total += pkg.torch.price

      if (pkg.accessories && pkg.accessories.length > 0) {
        pkg.accessories.forEach((accessory) => {
          if (accessory.price) total += accessory.price
        })
      }

      return total
    },
    []
  )

  const comparePackages = useCallback(
    (pkg1: EnhancedWeldingPackage, pkg2: EnhancedWeldingPackage) => {
      return {
        compatibility: {
          pkg1: pkg1.compatibility_confidence,
          pkg2: pkg2.compatibility_confidence,
          winner: pkg1.compatibility_confidence > pkg2.compatibility_confidence ? 'pkg1' : 'pkg2'
        },
        price: {
          pkg1: calculatePackageTotal(pkg1),
          pkg2: calculatePackageTotal(pkg2),
          winner: calculatePackageTotal(pkg1) < calculatePackageTotal(pkg2) ? 'pkg1' : 'pkg2'
        },
        validation: {
          pkg1: pkg1.metadata?.validation_score || 0,
          pkg2: pkg2.metadata?.validation_score || 0,
          winner: (pkg1.metadata?.validation_score || 0) > (pkg2.metadata?.validation_score || 0) ? 'pkg1' : 'pkg2'
        }
      }
    },
    [calculatePackageTotal]
  )

  const getPackagesByCategory = useCallback(() => {
    const categories: Record<string, EnhancedWeldingPackage[]> = {}
    
    packages.forEach(pkg => {
      const category = pkg.powersource.category || 'Other'
      if (!categories[category]) {
        categories[category] = []
      }
      categories[category].push(pkg)
    })

    return categories
  }, [packages])

  return {
    packages,
    selectedPackage,
    selectPackage,
    calculatePackageTotal,
    comparePackages,
    getPackagesByCategory
  }
}

export default useEnhancedConversation