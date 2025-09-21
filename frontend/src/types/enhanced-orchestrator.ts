/**
 * Enhanced Orchestrator Types
 * Types for integration with the enhanced orchestrator backend
 */

// Enhanced Orchestrator Request/Response Types
export interface EnhancedOrchestratorRequest {
  message: string
  user_id: string
  session_id?: string
  language: string
  flow_type: 'quick_package' | 'guided_flow'
  context?: Record<string, any>
  enable_observability?: boolean
}

export interface EnhancedOrchestratorResponse {
  status: 'success' | 'error' | 'partial_success' | 'success_with_warnings'
  timestamp: string
  session_id: string
  user_id: string
  processing_time_ms: number
  flow_type: string
  data: {
    packages: EnhancedWeldingPackage[]
    package_count: number
    selected_language: string
    ui_translations: Record<string, string>
    current_step?: string
    next_step?: string
    step_by_step_options?: any
  }
  metadata: {
    orchestrator_type: 'enhanced'
    orchestrator_version: string
    current_flow_state: string
    validation_score: number
    recommendation_confidence: number
    compatibility_confidence: number
    agent_decisions_count: number
    enhanced_features: {
      flow_manager_used: boolean
      error_handler_used: boolean
      hierarchical_state: boolean
      observability_enabled: boolean
    }
  }
  errors?: string[]
  warnings?: string[]
}

// Enhanced Package Types
export interface EnhancedPackageComponent {
  product_id: string
  product_name: string
  category: string
  subcategory?: string
  manufacturer?: string
  description?: string
  price?: number
  specifications?: Record<string, any>
  compatibility_score?: number
  sales_frequency?: string
  sales_count?: number
}

export interface EnhancedWeldingPackage {
  package_id: string
  package_name?: string
  description?: string
  powersource: EnhancedPackageComponent
  feeder?: EnhancedPackageComponent
  cooler?: EnhancedPackageComponent
  torch?: EnhancedPackageComponent
  accessories: EnhancedPackageComponent[]
  total_price?: number
  compatibility_confidence: number
  recommendation_reason: string
  sales_evidence?: string
  metadata?: {
    validation_score?: number
    recommendation_method?: string
  }
}

// Agent Decision Types
export interface AgentDecision {
  agent_role: string
  timestamp: string
  decision: string
  confidence: number
  reasoning: string
  tools_used: string[]
  data_sources: string[]
}

// Workflow Status Types
export interface WorkflowStatus {
  workflow_state: {
    session_id: string
    status: 'processing' | 'completed' | 'error' | 'cancelled'
    current_flow_state: string
    processing_time_ms: number
    agent_count: number
    error_count: number
    warning_count: number
  }
  session_metrics: {
    executions?: any[]
    performance_data?: any
    langgraph_checkpoints?: any[]
  }
  timestamp: string
}

// Conversation Context Types
export interface EnhancedConversationContext {
  sessionId: string
  userId: string
  currentFlowState: string
  workflowStatus: 'processing' | 'completed' | 'error' | 'cancelled'
  packages: EnhancedWeldingPackage[]
  processingTimeMs: number
  validationScore: number
  recommendationConfidence: number
  compatibilityConfidence: number
  agentDecisions: AgentDecision[]
  currentAgent?: string
  enhancedFeatures: {
    flowManagerUsed: boolean
    errorHandlerUsed: boolean
    hierarchicalState: boolean
    observabilityEnabled: boolean
  }
}

// Chat Message Types (Enhanced)
export interface EnhancedChatMessage {
  id: string
  content: string
  sender: 'user' | 'sparky'
  timestamp: string
  metadata?: {
    confidence?: number
    intent?: string
    mode?: 'guided' | 'expert'
    agent_decisions?: AgentDecision[]
    flow_state?: string
    error?: boolean
    processingTime?: number
    packages?: any[]
  }
}

// Observability Types
export interface LangSmithTraceData {
  trace_data: {
    traces: Array<{
      trace_id: string
      operation: string
      start_time: string
      metadata: Record<string, any>
      langsmith_run_id?: string
      parent_id?: string
    }>
    total_traces: number
    session_filter?: string
    langsmith_project: string
  }
  langsmith_status: {
    available: boolean
    client_initialized: boolean
    active_traces: number
    project: string
    tracing_enabled: boolean
  }
  timestamp: string
}

export interface PerformanceDashboardData {
  overview: {
    service_status: string
    total_requests: number
    success_rate: number
    average_response_time: number
    active_sessions: number
  }
  time_window: string
  timestamp: string
  agents?: {
    execution_counts: Record<string, number>
    agent_health: Record<string, any>
    error_rates: Record<string, number>
  }
  flows?: {
    state_counts: Record<string, number>
    flow_manager_health: any
    transition_success_rate: number
  }
  system_health?: {
    components: any
    observability_enabled: boolean
    langgraph_available: boolean
    error_recovery_rate: number
  }
}

// Error Types
export interface EnhancedError {
  type: string
  message: string
  agent_context?: string
  flow_state?: string
  recovery_suggestions?: string[]
  trace_id?: string
  timestamp?: string
}

// Service Response Types
export interface EnhancedServiceStatus {
  service: {
    type: 'enhanced'
    status: string
    initialized: boolean
    metrics: Record<string, any>
    observability_enabled: boolean
  }
  orchestrator: Record<string, any>
  health: Record<string, any>
  observability: Record<string, any>
  error_handling: Record<string, any>
}

// Conversation Context Types
export interface ConversationContext {
  sessionId: string
  userId: string
  currentMode: 'guided' | 'expert'
  extractedRequirements: WeldingRequirements
  conversationHistory: EnhancedChatMessage[]
}

export interface WeldingRequirements {
  process?: string
  material?: string
  thickness?: number
  current?: number
  voltage?: number
  cooling?: string
  portability?: string
}

// Agent Decision Timeline Types
export interface AgentDecisionTimelineEvent {
  timestamp: string
  event_type: 'workflow_start' | 'agent_execution' | 'flow_transition' | 'error' | 'completion'
  agent_name?: string
  flow_state?: string
  status?: string
  confidence?: number
  reasoning?: string
  tools_used?: string[]
  data_sources?: string[]
  processing_time_ms?: number
  error_message?: string
}

export interface AgentDecisionTimeline {
  session_id: string
  timeline: AgentDecisionTimelineEvent[]
  timestamp: string
}

// Session Metrics Types
export interface SessionMetrics {
  session_id: string
  executions: AgentExecution[]
  performance_data: PerformanceData
  langgraph_checkpoints: LangGraphCheckpoint[]
  timestamp: string
}

export interface AgentExecution {
  agent_name: string
  timestamp: string
  flow_state: string
  confidence: number
  reasoning: string
  tools_used: string[]
  data_sources: string[]
  execution_time_ms: number
  success: boolean
  error_message?: string
}

export interface PerformanceData {
  total_execution_time_ms: number
  agent_count: number
  success_rate: number
  error_count: number
  warning_count: number
  cache_hit_rate: number
}

export interface LangGraphCheckpoint {
  checkpoint_id: string
  timestamp: string
  flow_state: string
  metadata: Record<string, any>
}

// Enhanced Service Status Types
export interface EnhancedServiceHealth {
  orchestrator: 'healthy' | 'degraded' | 'unhealthy'
  flow_manager: 'healthy' | 'degraded' | 'unhealthy'
  error_handler: 'healthy' | 'degraded' | 'unhealthy'
  observability: 'healthy' | 'degraded' | 'unhealthy'
  agents: Record<string, 'healthy' | 'degraded' | 'unhealthy'>
}

// LangGraph Metrics Types
export interface LangGraphMetrics {
  service_langgraph: {
    available: boolean
    tracing_enabled: boolean
    agent_registry_status: string
    wrapper_execution_count: number
  }
  orchestrator_langgraph: {
    langgraph_integration: boolean
    checkpoint_available: boolean
    trace_count: number
    error_count: number
  }
  timestamp: string
}

// Cost Tracking Types
export interface CostTrackingData {
  cost_data: {
    total_cost: number
    cost_by_model: Record<string, number>
    cost_by_agent: Record<string, number>
    token_usage: {
      total_tokens: number
      input_tokens: number
      output_tokens: number
    }
    session_costs: Array<{
      session_id: string
      cost: number
      token_count: number
      timestamp: string
    }>
  }
  timestamp: string
  note?: string
}