/**
 * Enhanced Orchestrator Service
 * Service layer for integration with the enhanced orchestrator backend
 */

import { api } from '@services/api/client'
import { API_ENDPOINTS } from '@services/api/endpoints'
import {
  EnhancedOrchestratorRequest,
  EnhancedOrchestratorResponse,
  WorkflowStatus,
  LangSmithTraceData,
  PerformanceDashboardData,
  EnhancedServiceStatus,
  EnhancedError,
  SessionMetrics,
  AgentDecisionTimeline
} from '../../types/enhanced-orchestrator'

export class EnhancedOrchestratorService {
  private cache = new Map<string, { data: any; timestamp: number }>()
  private readonly CACHE_TTL = 5 * 60 * 1000 // 5 minutes
  private requestCount = 0
  private cacheHits = 0

  /**
   * Process a recommendation request through the enhanced orchestrator
   */
  async processRecommendationRequest(
    request: EnhancedOrchestratorRequest
  ): Promise<EnhancedOrchestratorResponse> {
    // Validate request before processing
    this.validateRequest(request)
    
    const cacheKey = this.generateCacheKey(request)
    this.requestCount++
    
    // Check cache first
    const cached = this.getFromCache(cacheKey)
    if (cached) {
      this.cacheHits++
      return cached
    }

    try {
      const response = await api.post<EnhancedOrchestratorResponse>(
        API_ENDPOINTS.ENHANCED_ORCHESTRATOR.PROCESS,
        {
          message: request.message,
          user_id: request.user_id || 'anonymous',
          session_id: request.session_id,
          language: request.language || 'en',
          flow_type: request.flow_type || 'quick_package',
          context: request.context,
          enable_observability: request.enable_observability ?? true
        }
      )

      // Cache successful response
      this.setCache(cacheKey, response)
      
      return response

    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Get workflow status for a specific session
   */
  async getWorkflowStatus(sessionId: string): Promise<WorkflowStatus> {
    try {
      return await api.get<WorkflowStatus>(
        API_ENDPOINTS.ENHANCED_ORCHESTRATOR.WORKFLOW_STATUS(sessionId)
      )
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Cancel a running workflow
   */
  async cancelWorkflow(sessionId: string): Promise<void> {
    try {
      await api.post(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.WORKFLOW_CANCEL(sessionId))
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Get LangGraph metrics and status
   */
  async getLangGraphMetrics(): Promise<any> {
    try {
      return await api.get(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.LANGGRAPH_METRICS)
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Enable or disable LangGraph tracing
   */
  async enableLangGraphTracing(enabled: boolean): Promise<void> {
    try {
      await api.post(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.LANGGRAPH_TRACING, {
        enabled
      })
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Get LangSmith trace data
   */
  async getLangSmithTraces(
    sessionId?: string,
    limit: number = 100,
    startTime?: string,
    endTime?: string
  ): Promise<LangSmithTraceData> {
    try {
      const params: Record<string, any> = { limit }
      if (sessionId) params.session_id = sessionId
      if (startTime) params.start_time = startTime
      if (endTime) params.end_time = endTime

      return await api.get(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.LANGSMITH_TRACES, {
        params
      })
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Get cost tracking data
   */
  async getCostTrackingData(
    sessionId?: string,
    startTime?: string,
    endTime?: string
  ): Promise<any> {
    try {
      const params: Record<string, any> = {}
      if (sessionId) params.session_id = sessionId
      if (startTime) params.start_time = startTime
      if (endTime) params.end_time = endTime

      return await api.get(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.LANGSMITH_COSTS, {
        params
      })
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Get performance dashboard data
   */
  async getPerformanceDashboard(
    timeWindow: string = '1h',
    includeAgents: boolean = true,
    includeFlows: boolean = true
  ): Promise<PerformanceDashboardData> {
    try {
      return await api.get(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.PERFORMANCE_DASHBOARD, {
        params: {
          time_window: timeWindow,
          include_agents: includeAgents,
          include_flows: includeFlows
        }
      })
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Get enhanced service status
   */
  async getServiceStatus(): Promise<EnhancedServiceStatus> {
    try {
      return await api.get(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.SERVICE_STATUS)
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Perform health check
   */
  async getHealthCheck(
    includePerformance: boolean = true,
    includeAgents: boolean = true,
    includeObservability: boolean = true
  ): Promise<any> {
    try {
      return await api.get(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.HEALTH_CHECK, {
        params: {
          include_performance: includePerformance,
          include_agents: includeAgents,
          include_observability: includeObservability
        }
      })
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Handle service errors with enhanced context and agent-level error information
   */
  private handleServiceError(error: any): EnhancedError {
    const enhancedError: EnhancedError = {
      type: 'unknown_error',
      message: 'An unexpected error occurred'
    }

    // Network connectivity issues
    if (!navigator.onLine) {
      enhancedError.type = 'network_error'
      enhancedError.message = 'No internet connection. Please check your network.'
      enhancedError.recovery_suggestions = [
        'Check your internet connection',
        'Try again when online',
        'Enable offline mode if available'
      ]
      return enhancedError
    }

    // No response (network timeout, server unreachable)
    if (!error.response) {
      enhancedError.type = 'network_error'
      enhancedError.message = 'Unable to reach the server. Please try again.'
      enhancedError.recovery_suggestions = [
        'Check your internet connection',
        'Verify server is running',
        'Try again in a few moments'
      ]
      return enhancedError
    }

    const status = error.response.status
    const data = error.response.data

    // Rate limiting
    if (status === 429) {
      enhancedError.type = 'rate_limit_error'
      enhancedError.message = 'Too many requests. Please wait before trying again.'
      enhancedError.recovery_suggestions = [
        'Wait 60 seconds before retrying',
        'Reduce request frequency',
        'Consider upgrading your plan'
      ]
      return enhancedError
    }

    // Server errors (5xx)
    if (status >= 500) {
      enhancedError.type = 'server_error'
      enhancedError.message = data?.message || 'Server error. Our team has been notified.'
      enhancedError.agent_context = data?.agent_context
      enhancedError.flow_state = data?.flow_state
      enhancedError.trace_id = data?.trace_id
      enhancedError.recovery_suggestions = [
        'Try again in a few minutes',
        'Check system status page',
        'Contact support if issue persists'
      ]
      return enhancedError
    }

    // Client errors (4xx)
    if (status >= 400 && status < 500) {
      if (status === 400) {
        enhancedError.type = 'validation_error'
        enhancedError.message = data?.message || 'Invalid request format'
        enhancedError.recovery_suggestions = [
          'Check your input format',
          'Ensure all required fields are provided',
          'Verify data types are correct'
        ]
      } else if (status === 401) {
        enhancedError.type = 'authentication_error'
        enhancedError.message = 'Authentication failed. Please log in again.'
        enhancedError.recovery_suggestions = [
          'Log in again',
          'Check your credentials',
          'Clear browser cache and cookies'
        ]
      } else if (status === 403) {
        enhancedError.type = 'authorization_error'
        enhancedError.message = 'You do not have permission to perform this action.'
        enhancedError.recovery_suggestions = [
          'Contact your administrator',
          'Check your user permissions',
          'Try logging out and back in'
        ]
      } else if (status === 404) {
        enhancedError.type = 'not_found_error'
        enhancedError.message = 'The requested resource was not found.'
        enhancedError.recovery_suggestions = [
          'Check the URL or resource ID',
          'Verify the resource exists',
          'Try refreshing the page'
        ]
      } else {
        enhancedError.type = 'client_error'
        enhancedError.message = data?.message || `Client error (${status})`
        enhancedError.recovery_suggestions = [
          'Check your request',
          'Try again',
          'Contact support if issue persists'
        ]
      }
    }

    // Enhanced orchestrator specific error handling
    if (data) {
      // Extract enhanced orchestrator error details
      if (data.error) {
        enhancedError.type = data.error.type || enhancedError.type
        enhancedError.message = data.error.message || enhancedError.message
        enhancedError.agent_context = data.error.agent_context
        enhancedError.flow_state = data.error.flow_state
        enhancedError.trace_id = data.error.trace_id
        enhancedError.recovery_suggestions = data.error.recovery_suggestions || enhancedError.recovery_suggestions
      }

      // Extract agent-specific error information
      if (data.agent_errors && Array.isArray(data.agent_errors)) {
        enhancedError.agent_context = data.agent_errors.map((agentError: any) => ({
          agent: agentError.agent_name,
          error: agentError.error_message,
          timestamp: agentError.timestamp,
          recovery_action: agentError.recovery_action
        })).join('; ')
      }

      // Extract workflow state information
      if (data.workflow_state) {
        enhancedError.flow_state = data.workflow_state.current_state
      }

      // Extract observability information
      if (data.trace_id) {
        enhancedError.trace_id = data.trace_id
      }

      // Handle specific enhanced orchestrator error types
      if (data.error_type === 'agent_timeout') {
        enhancedError.type = 'timeout_error'
        enhancedError.message = 'Request timed out while processing. Please try again.'
        enhancedError.recovery_suggestions = [
          'Try again with a simpler request',
          'Break down complex requests into smaller parts',
          'Check system load and try again later'
        ]
      } else if (data.error_type === 'agent_failure') {
        enhancedError.type = 'agent_error'
        enhancedError.message = `Agent processing failed: ${data.message || 'Unknown agent error'}`
        enhancedError.recovery_suggestions = [
          'Try rephrasing your request',
          'Provide more specific information',
          'Try again in a few moments'
        ]
      } else if (data.error_type === 'workflow_error') {
        enhancedError.type = 'workflow_error'
        enhancedError.message = `Workflow error: ${data.message || 'Workflow processing failed'}`
        enhancedError.recovery_suggestions = [
          'Start a new conversation',
          'Try a different approach',
          'Contact support if issue persists'
        ]
      }
    }

    // Add timestamp for debugging
    enhancedError.timestamp = new Date().toISOString()

    return enhancedError
  }

  /**
   * Generate cache key for requests
   */
  private generateCacheKey(request: EnhancedOrchestratorRequest): string {
    const keyData = {
      message: request.message,
      user_id: request.user_id,
      language: request.language,
      flow_type: request.flow_type
    }
    return `enhanced_orchestrator:${btoa(JSON.stringify(keyData))}`
  }

  /**
   * Get data from cache
   */
  private getFromCache(key: string): any | null {
    const cached = this.cache.get(key)
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      return cached.data
    }
    this.cache.delete(key)
    return null
  }

  /**
   * Set data in cache
   */
  private setCache(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() })
    
    // Clean up old cache entries
    if (this.cache.size > 100) {
      const oldestKey = this.cache.keys().next().value
      if (oldestKey) {
        this.cache.delete(oldestKey)
      }
    }
  }

  /**
   * Clear all cached data
   */
  clearCache(): void {
    this.cache.clear()
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; hitRate: number } {
    const hitRate = this.requestCount > 0 ? (this.cacheHits / this.requestCount) * 100 : 0
    return {
      size: this.cache.size,
      hitRate: Math.round(hitRate * 100) / 100
    }
  }

  /**
   * Validate request before sending
   */
  private validateRequest(request: EnhancedOrchestratorRequest): void {
    if (!request.message || request.message.trim().length === 0) {
      throw new Error('Message is required and cannot be empty')
    }

    if (request.message.length > 10000) {
      throw new Error('Message is too long (maximum 10,000 characters)')
    }

    if (request.user_id && request.user_id.length > 100) {
      throw new Error('User ID is too long (maximum 100 characters)')
    }

    if (request.language && !/^[a-z]{2}(-[A-Z]{2})?$/.test(request.language)) {
      throw new Error('Invalid language format (expected: en, en-US, etc.)')
    }

    if (request.flow_type && !['quick_package', 'guided_flow'].includes(request.flow_type)) {
      throw new Error('Invalid flow type (must be "quick_package" or "guided_flow")')
    }
  }

  /**
   * Process recommendation request with validation
   */
  async processRecommendationRequestSafe(
    request: EnhancedOrchestratorRequest
  ): Promise<EnhancedOrchestratorResponse> {
    // Validate request
    this.validateRequest(request)

    // Add default values
    const processedRequest: EnhancedOrchestratorRequest = {
      ...request,
      user_id: request.user_id || 'anonymous',
      language: request.language || 'en',
      flow_type: request.flow_type || 'quick_package',
      enable_observability: request.enable_observability ?? true
    }

    return this.processRecommendationRequest(processedRequest)
  }

  /**
   * Check service health and connectivity
   */
  async checkConnectivity(): Promise<boolean> {
    try {
      await this.getHealthCheck(false, false, false)
      return true
    } catch (error) {
      return false
    }
  }

  /**
   * Get session metrics for a specific session
   */
  async getSessionMetrics(sessionId: string): Promise<SessionMetrics> {
    try {
      return await api.get<SessionMetrics>(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.SESSION_METRICS(sessionId))
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Get enhanced performance metrics
   */
  async getEnhancedPerformanceMetrics(): Promise<any> {
    try {
      return await api.get(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.PERFORMANCE_METRICS)
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Validate flow configuration
   */
  async validateFlowConfiguration(): Promise<any> {
    try {
      return await api.get(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.FLOW_VALIDATION)
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Get workflow checkpoints for a session
   */
  async getWorkflowCheckpoints(sessionId: string): Promise<any> {
    try {
      return await api.get(API_ENDPOINTS.ENHANCED_ORCHESTRATOR.WORKFLOW_CHECKPOINTS(sessionId))
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Get agent decision timeline for a session
   */
  async getAgentDecisionTimeline(sessionId: string): Promise<AgentDecisionTimeline> {
    try {
      const workflowStatus = await this.getWorkflowStatus(sessionId)
      const sessionMetrics = await this.getSessionMetrics(sessionId)
      
      // Combine workflow status and session metrics to create decision timeline
      return {
        session_id: sessionId,
        timeline: this.extractDecisionTimeline(workflowStatus, sessionMetrics),
        timestamp: new Date().toISOString()
      }
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Extract decision timeline from workflow status and session metrics
   */
  private extractDecisionTimeline(workflowStatus: any, sessionMetrics: any): any[] {
    const timeline: any[] = []
    
    // Extract decisions from workflow state
    if (workflowStatus?.workflow_state) {
      const state = workflowStatus.workflow_state
      timeline.push({
        timestamp: workflowStatus.timestamp,
        event_type: 'workflow_start',
        flow_state: state.current_flow_state,
        status: state.status,
        processing_time_ms: state.processing_time_ms
      })
    }

    // Extract agent executions from session metrics
    if (sessionMetrics?.session_metrics?.executions) {
      sessionMetrics.session_metrics.executions.forEach((execution: any) => {
        timeline.push({
          timestamp: execution.timestamp || new Date().toISOString(),
          event_type: 'agent_execution',
          agent_name: execution.agent_name,
          flow_state: execution.flow_state,
          confidence: execution.confidence,
          reasoning: execution.reasoning,
          tools_used: execution.tools_used,
          data_sources: execution.data_sources
        })
      })
    }

    // Sort timeline by timestamp
    return timeline.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
  }

  /**
   * Get service information for debugging
   */
  getServiceInfo(): Record<string, any> {
    return {
      cacheSize: this.cache.size,
      cacheTTL: this.CACHE_TTL,
      serviceVersion: '1.0.0',
      lastActivity: new Date().toISOString(),
      requestCount: this.requestCount,
      cacheHitRate: this.getCacheStats().hitRate
    }
  }
}

// Export singleton instance
export const enhancedOrchestratorService = new EnhancedOrchestratorService()