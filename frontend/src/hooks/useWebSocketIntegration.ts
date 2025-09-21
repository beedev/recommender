/**
 * WebSocket Integration Hook
 * Manages WebSocket connection and real-time updates for enhanced orchestrator
 */

import { useEffect, useCallback } from 'react'
import { useAppDispatch, useAppSelector } from './redux'
import { enhancedOrchestratorWebSocket } from '@services/websocket'
import {
  connectWebSocket,
  disconnectWebSocket,
  setConnectionStatus,
  setReconnectAttempts,
  handleWorkflowStatusUpdate,
  handleAgentExecutionUpdate,
  handleTypingIndicatorUpdate,
  handleRecommendationUpdate,
  setError
} from '@store/slices/enhancedConversationSlice'

export interface UseWebSocketIntegrationOptions {
  autoConnect?: boolean
  enableReconnect?: boolean
  maxReconnectAttempts?: number
}

export const useWebSocketIntegration = (options: UseWebSocketIntegrationOptions = {}) => {
  const {
    autoConnect = true,
    enableReconnect = true,
    maxReconnectAttempts = 5
  } = options

  const dispatch = useAppDispatch()
  const {
    sessionId,
    connectionStatus,
    reconnectAttempts,
    realTimeUpdatesEnabled
  } = useAppSelector(state => state.enhancedConversation)

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(async (sessionIdOverride?: string) => {
    const targetSessionId = sessionIdOverride || sessionId
    if (!targetSessionId) {
      console.warn('Cannot connect WebSocket: No session ID available')
      return
    }

    try {
      await dispatch(connectWebSocket(targetSessionId)).unwrap()
    } catch (error) {
      console.error('Failed to connect WebSocket:', error)
    }
  }, [dispatch, sessionId])

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(async () => {
    try {
      await dispatch(disconnectWebSocket()).unwrap()
    } catch (error) {
      console.error('Failed to disconnect WebSocket:', error)
    }
  }, [dispatch])

  /**
   * Setup WebSocket event handlers
   */
  const setupEventHandlers = useCallback(() => {
    // Connection status updates
    const unsubscribeStatus = enhancedOrchestratorWebSocket.onConnectionStatusChange((status) => {
      dispatch(setConnectionStatus(status.status))
      dispatch(setReconnectAttempts(status.reconnectAttempts))
    })

    // Workflow status updates
    const unsubscribeWorkflow = enhancedOrchestratorWebSocket.onWorkflowStatusUpdate((update) => {
      dispatch(handleWorkflowStatusUpdate(update))
    })

    // Agent execution updates
    const unsubscribeAgent = enhancedOrchestratorWebSocket.onAgentExecutionUpdate((update) => {
      dispatch(handleAgentExecutionUpdate(update))
    })

    // Typing indicator updates
    const unsubscribeTyping = enhancedOrchestratorWebSocket.onTypingIndicatorUpdate((update) => {
      dispatch(handleTypingIndicatorUpdate(update))
    })

    // Recommendation updates
    const unsubscribeRecommendation = enhancedOrchestratorWebSocket.onRecommendationUpdate((update) => {
      dispatch(handleRecommendationUpdate(update))
    })

    // Error handling
    const unsubscribeError = enhancedOrchestratorWebSocket.on('error', (errorData) => {
      dispatch(setError({
        type: 'websocket_error',
        message: errorData.message || 'WebSocket error occurred',
        recovery_suggestions: ['Try refreshing the page', 'Check your internet connection']
      }))
    })

    return () => {
      unsubscribeStatus()
      unsubscribeWorkflow()
      unsubscribeAgent()
      unsubscribeTyping()
      unsubscribeRecommendation()
      unsubscribeError()
    }
  }, [dispatch])

  /**
   * Handle reconnection logic
   */
  const handleReconnection = useCallback(() => {
    if (!enableReconnect || !sessionId) return

    if (connectionStatus === 'error' && reconnectAttempts < maxReconnectAttempts) {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000) // Exponential backoff, max 30s
      
      setTimeout(() => {
        console.log(`Attempting WebSocket reconnection (${reconnectAttempts + 1}/${maxReconnectAttempts})`)
        connect()
      }, delay)
    }
  }, [enableReconnect, sessionId, connectionStatus, reconnectAttempts, maxReconnectAttempts, connect])

  /**
   * Send typing indicator
   */
  const sendTypingIndicator = useCallback((isTyping: boolean) => {
    if (connectionStatus === 'connected') {
      enhancedOrchestratorWebSocket.sendTypingIndicator(isTyping)
    }
  }, [connectionStatus])

  /**
   * Cancel workflow
   */
  const cancelWorkflow = useCallback(() => {
    if (connectionStatus === 'connected') {
      enhancedOrchestratorWebSocket.sendWorkflowCancellation()
    }
  }, [connectionStatus])

  /**
   * Request workflow status
   */
  const requestWorkflowStatus = useCallback(() => {
    if (connectionStatus === 'connected') {
      enhancedOrchestratorWebSocket.requestWorkflowStatus()
    }
  }, [connectionStatus])

  // Setup event handlers on mount
  useEffect(() => {
    if (!realTimeUpdatesEnabled) return

    const cleanup = setupEventHandlers()
    return cleanup
  }, [setupEventHandlers, realTimeUpdatesEnabled])

  // Auto-connect when session ID is available
  useEffect(() => {
    if (autoConnect && sessionId && connectionStatus === 'disconnected' && realTimeUpdatesEnabled) {
      connect()
    }
  }, [autoConnect, sessionId, connectionStatus, realTimeUpdatesEnabled, connect])

  // Handle reconnection attempts
  useEffect(() => {
    handleReconnection()
  }, [handleReconnection])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (connectionStatus === 'connected') {
        disconnect()
      }
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return {
    // Connection state
    connectionStatus,
    reconnectAttempts,
    isConnected: connectionStatus === 'connected',
    isConnecting: connectionStatus === 'connecting',
    
    // Connection methods
    connect,
    disconnect,
    
    // Real-time features
    sendTypingIndicator,
    cancelWorkflow,
    requestWorkflowStatus,
    
    // WebSocket service stats
    getStats: () => enhancedOrchestratorWebSocket.getStats()
  }
}

export default useWebSocketIntegration