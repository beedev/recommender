/**
 * WebSocket Services Export
 */

export { WebSocketService, webSocketService } from './WebSocketService'
export { EnhancedOrchestratorWebSocket, enhancedOrchestratorWebSocket } from './EnhancedOrchestratorWebSocket'

export type {
  WebSocketMessage,
  WebSocketConnectionStatus,
  WebSocketEventHandler
} from './WebSocketService'

export type {
  WorkflowStatusUpdate,
  AgentExecutionUpdate,
  TypingIndicatorUpdate,
  RecommendationUpdate,
  EnhancedOrchestratorEventHandler
} from './EnhancedOrchestratorWebSocket'