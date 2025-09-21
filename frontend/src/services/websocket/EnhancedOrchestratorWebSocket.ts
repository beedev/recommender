/**
 * Enhanced Orchestrator WebSocket Service
 * Specialized WebSocket service for real-time enhanced orchestrator updates
 */

import { WebSocketService, WebSocketMessage } from './WebSocketService'
import { 
  WorkflowStatus, 
  AgentDecisionTimelineEvent,
  EnhancedChatMessage 
} from '../../types/enhanced-orchestrator'

export interface WorkflowStatusUpdate {
  session_id: string
  status: 'processing' | 'completed' | 'error' | 'cancelled'
  current_flow_state: string
  processing_time_ms: number
  agent_count: number
  error_count: number
  warning_count: number
}

export interface AgentExecutionUpdate {
  session_id: string
  agent_name: string
  flow_state: string
  status: 'started' | 'completed' | 'error'
  confidence?: number
  reasoning?: string
  processing_time_ms?: number
  error_message?: string
}

export interface TypingIndicatorUpdate {
  session_id: string
  is_typing: boolean
  agent_name?: string
  estimated_completion_time?: number
}

export interface RecommendationUpdate {
  session_id: string
  packages: any[]
  confidence: number
  reasoning: string
  agent_decisions: AgentDecisionTimelineEvent[]
}

export type EnhancedOrchestratorEventHandler<T = any> = (data: T) => void

export class EnhancedOrchestratorWebSocket {
  private wsService: WebSocketService
  private sessionId: string | null = null
  private eventHandlers = new Map<string, Set<EnhancedOrchestratorEventHandler>>()

  constructor(wsService: WebSocketService) {
    this.wsService = wsService
    this.setupEventHandlers()
  }

  /**
   * Connect to enhanced orchestrator WebSocket with session ID
   */
  async connect(sessionId: string): Promise<void> {
    this.sessionId = sessionId
    await this.wsService.connect(sessionId)
    
    // Subscribe to session-specific updates
    this.subscribeToSession(sessionId)
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    this.sessionId = null
    this.wsService.disconnect()
  }

  /**
   * Subscribe to workflow status updates
   */
  onWorkflowStatusUpdate(handler: EnhancedOrchestratorEventHandler<WorkflowStatusUpdate>): () => void {
    return this.on('workflow_status_update', handler)
  }

  /**
   * Subscribe to agent execution updates
   */
  onAgentExecutionUpdate(handler: EnhancedOrchestratorEventHandler<AgentExecutionUpdate>): () => void {
    return this.on('agent_execution_update', handler)
  }

  /**
   * Subscribe to typing indicator updates
   */
  onTypingIndicatorUpdate(handler: EnhancedOrchestratorEventHandler<TypingIndicatorUpdate>): () => void {
    return this.on('typing_indicator_update', handler)
  }

  /**
   * Subscribe to recommendation updates
   */
  onRecommendationUpdate(handler: EnhancedOrchestratorEventHandler<RecommendationUpdate>): () => void {
    return this.on('recommendation_update', handler)
  }

  /**
   * Subscribe to connection status changes
   */
  onConnectionStatusChange(handler: EnhancedOrchestratorEventHandler<any>): () => void {
    return this.wsService.onStatusChange(handler)
  }

  /**
   * Get current connection status
   */
  getConnectionStatus() {
    return this.wsService.getConnectionStatus()
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.wsService.isConnected()
  }

  /**
   * Send typing indicator
   */
  sendTypingIndicator(isTyping: boolean): void {
    if (!this.sessionId) return

    this.wsService.send({
      type: 'typing_indicator',
      data: {
        session_id: this.sessionId,
        is_typing: isTyping,
        user_typing: true
      }
    })
  }

  /**
   * Send workflow cancellation request
   */
  sendWorkflowCancellation(): void {
    if (!this.sessionId) return

    this.wsService.send({
      type: 'cancel_workflow',
      data: {
        session_id: this.sessionId
      }
    })
  }

  /**
   * Request workflow status update
   */
  requestWorkflowStatus(): void {
    if (!this.sessionId) return

    this.wsService.send({
      type: 'get_workflow_status',
      data: {
        session_id: this.sessionId
      }
    })
  }

  /**
   * Subscribe to events
   */
  private on<T>(eventType: string, handler: EnhancedOrchestratorEventHandler<T>): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set())
    }

    this.eventHandlers.get(eventType)!.add(handler)

    return () => {
      const handlers = this.eventHandlers.get(eventType)
      if (handlers) {
        handlers.delete(handler)
        if (handlers.size === 0) {
          this.eventHandlers.delete(eventType)
        }
      }
    }
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    this.wsService.on('message', (message: WebSocketMessage) => {
      this.handleEnhancedOrchestratorMessage(message)
    })
  }

  /**
   * Handle enhanced orchestrator specific messages
   */
  private handleEnhancedOrchestratorMessage(message: WebSocketMessage): void {
    // Filter messages for current session
    if (this.sessionId && message.session_id && message.session_id !== this.sessionId) {
      return
    }

    // Route message to appropriate handlers
    const handlers = this.eventHandlers.get(message.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.data)
        } catch (error) {
          console.error(`Error in enhanced orchestrator event handler for ${message.type}:`, error)
        }
      })
    }

    // Handle specific message types
    switch (message.type) {
      case 'workflow_status_update':
        this.handleWorkflowStatusUpdate(message.data)
        break
      case 'agent_execution_update':
        this.handleAgentExecutionUpdate(message.data)
        break
      case 'typing_indicator_update':
        this.handleTypingIndicatorUpdate(message.data)
        break
      case 'recommendation_update':
        this.handleRecommendationUpdate(message.data)
        break
      case 'error':
        this.handleError(message.data)
        break
    }
  }

  /**
   * Handle workflow status updates
   */
  private handleWorkflowStatusUpdate(data: WorkflowStatusUpdate): void {
    console.log('Workflow status update:', data)
    
    // Emit to specific handlers
    const handlers = this.eventHandlers.get('workflow_status_update')
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }
  }

  /**
   * Handle agent execution updates
   */
  private handleAgentExecutionUpdate(data: AgentExecutionUpdate): void {
    console.log('Agent execution update:', data)
    
    // Emit to specific handlers
    const handlers = this.eventHandlers.get('agent_execution_update')
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }
  }

  /**
   * Handle typing indicator updates
   */
  private handleTypingIndicatorUpdate(data: TypingIndicatorUpdate): void {
    // Emit to specific handlers
    const handlers = this.eventHandlers.get('typing_indicator_update')
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }
  }

  /**
   * Handle recommendation updates
   */
  private handleRecommendationUpdate(data: RecommendationUpdate): void {
    console.log('Recommendation update:', data)
    
    // Emit to specific handlers
    const handlers = this.eventHandlers.get('recommendation_update')
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }
  }

  /**
   * Handle error messages
   */
  private handleError(data: any): void {
    console.error('Enhanced orchestrator WebSocket error:', data)
    
    // Emit to error handlers
    const handlers = this.eventHandlers.get('error')
    if (handlers) {
      handlers.forEach(handler => handler(data))
    }
  }

  /**
   * Subscribe to session-specific updates
   */
  private subscribeToSession(sessionId: string): void {
    this.wsService.send({
      type: 'subscribe_session',
      data: {
        session_id: sessionId,
        events: [
          'workflow_status_update',
          'agent_execution_update',
          'typing_indicator_update',
          'recommendation_update',
          'error'
        ]
      }
    })
  }

  /**
   * Get service statistics
   */
  getStats(): Record<string, any> {
    return {
      ...this.wsService.getStats(),
      sessionId: this.sessionId,
      enhancedEventHandlerCount: Array.from(this.eventHandlers.values())
        .reduce((total, handlers) => total + handlers.size, 0),
      enhancedEventTypes: Array.from(this.eventHandlers.keys())
    }
  }
}

// Export singleton instance
export const enhancedOrchestratorWebSocket = new EnhancedOrchestratorWebSocket(
  new WebSocketService()
)