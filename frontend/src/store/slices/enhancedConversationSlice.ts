import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { sparkyService } from '@services/sparky/sparkyService'
import { enhancedOrchestratorService } from '@services/enhanced-orchestrator/enhancedOrchestratorService'
import { 
  enhancedOrchestratorWebSocket,
  WorkflowStatusUpdate,
  AgentExecutionUpdate,
  TypingIndicatorUpdate,
  RecommendationUpdate
} from '@services/websocket'
import {
  EnhancedOrchestratorRequest,
  // EnhancedOrchestratorResponse,
  EnhancedWeldingPackage,
  EnhancedChatMessage,
  EnhancedError,
  AgentDecision
  // WorkflowStatus,
  // EnhancedConversationContext
} from '../../types/enhanced-orchestrator'

interface EnhancedConversationState {
  // Conversation state
  sessionId: string | null
  userId: string
  messages: EnhancedChatMessage[]
  currentFlowState: string
  workflowStatus: 'processing' | 'completed' | 'error' | 'cancelled' | 'idle'
  
  // Package recommendations
  packages: EnhancedWeldingPackage[]
  selectedPackage: EnhancedWeldingPackage | null
  processingTimeMs: number
  validationScore: number
  recommendationConfidence: number
  compatibilityConfidence: number
  
  // Agent metadata
  agentDecisions: AgentDecision[]
  currentAgent: string | null
  enhancedFeatures: {
    flowManagerUsed: boolean
    errorHandlerUsed: boolean
    hierarchicalState: boolean
    observabilityEnabled: boolean
  }
  
  // UI state
  isLoading: boolean
  isTyping: boolean
  error: EnhancedError | null
  warnings: string[]
  
  // Conversation mode
  conversationMode: 'guided' | 'expert' | 'unknown'
  isGuidedFlow: boolean
  
  // WebSocket connection state
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error'
  reconnectAttempts: number
  lastConnected: string | null
  realTimeUpdatesEnabled: boolean
  
  // Cache and performance
  lastActivity: string | null
  cacheHitRate: number
}

const initialState: EnhancedConversationState = {
  sessionId: null,
  userId: 'anonymous',
  messages: [],
  currentFlowState: 'initialization',
  workflowStatus: 'idle',
  
  packages: [],
  selectedPackage: null,
  processingTimeMs: 0,
  validationScore: 0,
  recommendationConfidence: 0,
  compatibilityConfidence: 0,
  
  agentDecisions: [],
  currentAgent: null,
  enhancedFeatures: {
    flowManagerUsed: false,
    errorHandlerUsed: false,
    hierarchicalState: false,
    observabilityEnabled: true
  },
  
  isLoading: false,
  isTyping: false,
  error: null,
  warnings: [],
  
  conversationMode: 'unknown',
  isGuidedFlow: false,
  
  connectionStatus: 'disconnected',
  reconnectAttempts: 0,
  lastConnected: null,
  realTimeUpdatesEnabled: true,
  
  lastActivity: null,
  cacheHitRate: 0
}

// Async thunks for enhanced orchestrator integration
export const sendEnhancedMessage = createAsyncThunk(
  'enhancedConversation/sendMessage',
  async (
    { 
      message, 
      flowType = 'quick_package',
      language = 'en',
      enableObservability = true 
    }: {
      message: string
      flowType?: 'quick_package' | 'guided_flow'
      language?: string
      enableObservability?: boolean
    },
    { getState, rejectWithValue }
  ) => {
    try {
      const state = getState() as { enhancedConversation: EnhancedConversationState }
      const currentState = state.enhancedConversation
      
      const request: EnhancedOrchestratorRequest = {
        message,
        user_id: currentState.userId,
        session_id: currentState.sessionId || `session-${Date.now()}`,
        language,
        flow_type: flowType,
        context: {
          conversation_history: currentState.messages.slice(-5), // Last 5 messages for context
          current_mode: currentState.conversationMode
        },
        enable_observability: enableObservability
      }

      const response = await enhancedOrchestratorService.processRecommendationRequestSafe(request)
      return { request, response }
    } catch (error: any) {
      return rejectWithValue(error)
    }
  }
)

export const getWorkflowStatus = createAsyncThunk(
  'enhancedConversation/getWorkflowStatus',
  async (sessionId: string, { rejectWithValue }) => {
    try {
      const status = await enhancedOrchestratorService.getWorkflowStatus(sessionId)
      return status
    } catch (error: any) {
      return rejectWithValue(error)
    }
  }
)

export const cancelWorkflow = createAsyncThunk(
  'enhancedConversation/cancelWorkflow',
  async (sessionId: string, { rejectWithValue }) => {
    try {
      await enhancedOrchestratorService.cancelWorkflow(sessionId)
      return sessionId
    } catch (error: any) {
      return rejectWithValue(error)
    }
  }
)

export const checkServiceHealth = createAsyncThunk(
  'enhancedConversation/checkServiceHealth',
  async (_, { rejectWithValue }) => {
    try {
      const isHealthy = await enhancedOrchestratorService.checkConnectivity()
      return isHealthy
    } catch (error: any) {
      return rejectWithValue(error)
    }
  }
)

export const connectWebSocket = createAsyncThunk(
  'enhancedConversation/connectWebSocket',
  async (sessionId: string, { rejectWithValue }) => {
    try {
      await enhancedOrchestratorWebSocket.connect(sessionId)
      return sessionId
    } catch (error: any) {
      return rejectWithValue(error)
    }
  }
)

export const disconnectWebSocket = createAsyncThunk(
  'enhancedConversation/disconnectWebSocket',
  async (_, { rejectWithValue }) => {
    try {
      enhancedOrchestratorWebSocket.disconnect()
      return true
    } catch (error: any) {
      return rejectWithValue(error)
    }
  }
)

const enhancedConversationSlice = createSlice({
  name: 'enhancedConversation',
  initialState,
  reducers: {
    // Message management
    addMessage: (state, action: PayloadAction<EnhancedChatMessage>) => {
      state.messages.push(action.payload)
      state.lastActivity = new Date().toISOString()
    },
    
    updateMessage: (state, action: PayloadAction<{ id: string; updates: Partial<EnhancedChatMessage> }>) => {
      const message = state.messages.find(msg => msg.id === action.payload.id)
      if (message) {
        Object.assign(message, action.payload.updates)
      }
    },
    
    removeMessage: (state, action: PayloadAction<string>) => {
      state.messages = state.messages.filter(msg => msg.id !== action.payload)
    },
    
    clearMessages: (state) => {
      state.messages = []
      state.lastActivity = new Date().toISOString()
    },
    
    // Session management
    setSessionId: (state, action: PayloadAction<string>) => {
      state.sessionId = action.payload
    },
    
    setUserId: (state, action: PayloadAction<string>) => {
      state.userId = action.payload
    },
    
    resetSession: (state) => {
      state.sessionId = null
      state.messages = []
      state.packages = []
      state.selectedPackage = null
      state.agentDecisions = []
      state.currentAgent = null
      state.workflowStatus = 'idle'
      state.currentFlowState = 'initialization'
      state.error = null
      state.warnings = []
      state.conversationMode = 'unknown'
      state.isGuidedFlow = false
    },
    
    // Package management
    setSelectedPackage: (state, action: PayloadAction<EnhancedWeldingPackage | null>) => {
      state.selectedPackage = action.payload
    },
    
    updatePackage: (state, action: PayloadAction<{ packageId: string; updates: Partial<EnhancedWeldingPackage> }>) => {
      const packageIndex = state.packages.findIndex(pkg => pkg.package_id === action.payload.packageId)
      if (packageIndex !== -1 && state.packages[packageIndex]) {
        Object.assign(state.packages[packageIndex], action.payload.updates)
      }
      
      if (state.selectedPackage?.package_id === action.payload.packageId) {
        Object.assign(state.selectedPackage, action.payload.updates)
      }
    },
    
    // UI state management
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    
    setTyping: (state, action: PayloadAction<boolean>) => {
      state.isTyping = action.payload
    },
    
    setConversationMode: (state, action: PayloadAction<'guided' | 'expert' | 'unknown'>) => {
      state.conversationMode = action.payload
    },
    
    setGuidedFlow: (state, action: PayloadAction<boolean>) => {
      state.isGuidedFlow = action.payload
    },
    
    // Error management
    setError: (state, action: PayloadAction<EnhancedError | null>) => {
      state.error = action.payload
    },
    
    clearError: (state) => {
      state.error = null
    },
    
    addWarning: (state, action: PayloadAction<string>) => {
      if (!state.warnings.includes(action.payload)) {
        state.warnings.push(action.payload)
      }
    },
    
    removeWarning: (state, action: PayloadAction<string>) => {
      state.warnings = state.warnings.filter(warning => warning !== action.payload)
    },
    
    clearWarnings: (state) => {
      state.warnings = []
    },
    
    // Agent decision tracking
    addAgentDecision: (state, action: PayloadAction<AgentDecision>) => {
      state.agentDecisions.push(action.payload)
      // Keep only last 20 decisions
      if (state.agentDecisions.length > 20) {
        state.agentDecisions = state.agentDecisions.slice(-20)
      }
    },
    
    setCurrentAgent: (state, action: PayloadAction<string | null>) => {
      state.currentAgent = action.payload
    },
    
    // Enhanced features
    updateEnhancedFeatures: (state, action: PayloadAction<Partial<EnhancedConversationState['enhancedFeatures']>>) => {
      Object.assign(state.enhancedFeatures, action.payload)
    },
    
    // Performance tracking
    updateCacheStats: (state, action: PayloadAction<{ hitRate: number }>) => {
      state.cacheHitRate = action.payload.hitRate
    },
    
    // WebSocket connection management
    setConnectionStatus: (state, action: PayloadAction<'connecting' | 'connected' | 'disconnected' | 'error'>) => {
      state.connectionStatus = action.payload
      if (action.payload === 'connected') {
        state.lastConnected = new Date().toISOString()
        state.reconnectAttempts = 0
      }
    },
    
    setReconnectAttempts: (state, action: PayloadAction<number>) => {
      state.reconnectAttempts = action.payload
    },
    
    setRealTimeUpdatesEnabled: (state, action: PayloadAction<boolean>) => {
      state.realTimeUpdatesEnabled = action.payload
    },
    
    // Real-time updates from WebSocket
    handleWorkflowStatusUpdate: (state, action: PayloadAction<WorkflowStatusUpdate>) => {
      const update = action.payload
      state.workflowStatus = update.status
      state.currentFlowState = update.current_flow_state
      state.processingTimeMs = update.processing_time_ms
    },
    
    handleAgentExecutionUpdate: (state, action: PayloadAction<AgentExecutionUpdate>) => {
      const update = action.payload
      state.currentAgent = update.agent_name
      state.currentFlowState = update.flow_state
      
      // Add agent decision if completed
      if (update.status === 'completed' && update.confidence && update.reasoning) {
        const decision: AgentDecision = {
          agent_role: update.agent_name,
          timestamp: new Date().toISOString(),
          decision: `Agent ${update.agent_name} completed processing`,
          confidence: update.confidence,
          reasoning: update.reasoning,
          tools_used: [],
          data_sources: []
        }
        state.agentDecisions.push(decision)
        
        // Keep only last 20 decisions
        if (state.agentDecisions.length > 20) {
          state.agentDecisions = state.agentDecisions.slice(-20)
        }
      }
    },
    
    handleTypingIndicatorUpdate: (state, action: PayloadAction<TypingIndicatorUpdate>) => {
      const update = action.payload
      state.isTyping = update.is_typing
      if (update.agent_name) {
        state.currentAgent = update.agent_name
      }
    },
    
    handleRecommendationUpdate: (state, action: PayloadAction<RecommendationUpdate>) => {
      const update = action.payload
      state.packages = update.packages
      state.recommendationConfidence = update.confidence
      
      // Add agent decisions from the update
      if (update.agent_decisions) {
        state.agentDecisions.push(...update.agent_decisions)
        // Keep only last 20 decisions
        if (state.agentDecisions.length > 20) {
          state.agentDecisions = state.agentDecisions.slice(-20)
        }
      }
      
      // Add Sparky message about new recommendations
      const sparkyMessage: EnhancedChatMessage = {
        id: Date.now().toString(),
        content: `I've updated your recommendations based on the latest analysis. Found ${update.packages.length} package${update.packages.length > 1 ? 's' : ''} that match your requirements.`,
        sender: 'sparky',
        timestamp: new Date().toISOString(),
        metadata: {
          confidence: update.confidence,
          mode: state.conversationMode,
          packages: update.packages
        }
      }
      state.messages.push(sparkyMessage)
    }
  },
  
  extraReducers: (builder) => {
    builder
      // Send enhanced message
      .addCase(sendEnhancedMessage.pending, (state, action) => {
        state.isLoading = true
        state.isTyping = true
        state.error = null
        state.workflowStatus = 'processing'
        
        // Add user message immediately
        const userMessage: EnhancedChatMessage = {
          id: Date.now().toString(),
          content: action.meta.arg.message,
          sender: 'user',
          timestamp: new Date().toISOString()
        }
        state.messages.push(userMessage)
      })
      
      .addCase(sendEnhancedMessage.fulfilled, (state, action) => {
        const { response } = action.payload
        
        state.isLoading = false
        state.isTyping = false
        state.workflowStatus = response.status === 'success' ? 'completed' : 'error'
        
        // Update session information
        state.sessionId = response.session_id
        state.currentFlowState = response.metadata.current_flow_state
        state.processingTimeMs = response.processing_time_ms
        state.validationScore = response.metadata.validation_score
        state.recommendationConfidence = response.metadata.recommendation_confidence
        state.compatibilityConfidence = response.metadata.compatibility_confidence
        
        // Update enhanced features
        if (response.metadata.enhanced_features) {
          state.enhancedFeatures = {
            flowManagerUsed: response.metadata.enhanced_features.flow_manager_used || false,
            errorHandlerUsed: response.metadata.enhanced_features.error_handler_used || false,
            hierarchicalState: response.metadata.enhanced_features.hierarchical_state || false,
            observabilityEnabled: response.metadata.enhanced_features.observability_enabled || false,
          }
        }
        
        // Determine conversation mode
        const isGuidedResponse = response.data.current_step && response.data.next_step
        const detectedMode = isGuidedResponse ? 'guided' : 'expert'
        state.conversationMode = detectedMode
        state.isGuidedFlow = Boolean(isGuidedResponse)
        
        // Create Sparky's response
        let sparkyContent = ''
        if (response.data.packages.length > 0) {
          sparkyContent = `Based on your requirements, I found ${response.data.packages.length} recommended package${response.data.packages.length > 1 ? 's' : ''} for you.`
        } else if (response.data.current_step) {
          sparkyContent = `Let me help you step by step. ${response.data.current_step}`
        } else {
          sparkyContent = "I understand your request. Let me analyze your requirements and find the best recommendations."
        }
        
        const sparkyMessage: EnhancedChatMessage = {
          id: (Date.now() + 1).toString(),
          content: sparkyContent,
          sender: 'sparky',
          timestamp: new Date().toISOString(),
          metadata: {
            confidence: response.metadata.recommendation_confidence,
            mode: detectedMode,
            flow_state: response.metadata.current_flow_state
          }
        }
        
        state.messages.push(sparkyMessage)
        
        // Update packages
        if (response.data.packages && response.data.packages.length > 0) {
          state.packages = response.data.packages
          state.selectedPackage = response.data.packages[0] || null
        }
        
        // Handle warnings
        if (response.warnings && response.warnings.length > 0) {
          state.warnings = [...state.warnings, ...response.warnings]
        }
        
        state.lastActivity = new Date().toISOString()
      })
      
      .addCase(sendEnhancedMessage.rejected, (state, action) => {
        state.isLoading = false
        state.isTyping = false
        state.workflowStatus = 'error'
        state.error = action.payload as EnhancedError
        
        // Add error message from Sparky
        const errorMessage: EnhancedChatMessage = {
          id: (Date.now() + 1).toString(),
          content: (action.payload as EnhancedError).message || "I'm having trouble processing your request right now. Please try again in a moment.",
          sender: 'sparky',
          timestamp: new Date().toISOString(),
          metadata: {
            confidence: 0.1,
            mode: 'expert'
          }
        }
        
        state.messages.push(errorMessage)
      })
      
      // Workflow status
      .addCase(getWorkflowStatus.fulfilled, (state, action) => {
        const status = action.payload
        state.workflowStatus = status.workflow_state.status
        state.currentFlowState = status.workflow_state.current_flow_state
        state.processingTimeMs = status.workflow_state.processing_time_ms
      })
      
      .addCase(getWorkflowStatus.rejected, (state, action) => {
        state.error = action.payload as EnhancedError
      })
      
      // Cancel workflow
      .addCase(cancelWorkflow.fulfilled, (state) => {
        state.workflowStatus = 'cancelled'
        state.isLoading = false
        state.isTyping = false
      })
      
      .addCase(cancelWorkflow.rejected, (state, action) => {
        state.error = action.payload as EnhancedError
      })
      
      // Service health check
      .addCase(checkServiceHealth.fulfilled, (state, action) => {
        // Update connection status based on health check
        if (!action.payload) {
          state.error = {
            type: 'service_unavailable',
            message: 'Enhanced orchestrator service is currently unavailable',
            recovery_suggestions: ['Try again in a few moments', 'Check your internet connection']
          }
        }
      })
      
      .addCase(checkServiceHealth.rejected, (state, action) => {
        state.error = action.payload as EnhancedError
      })
      
      // WebSocket connection
      .addCase(connectWebSocket.pending, (state) => {
        state.connectionStatus = 'connecting'
      })
      
      .addCase(connectWebSocket.fulfilled, (state, action) => {
        state.connectionStatus = 'connected'
        state.lastConnected = new Date().toISOString()
        state.reconnectAttempts = 0
        state.sessionId = action.payload
      })
      
      .addCase(connectWebSocket.rejected, (state, action) => {
        state.connectionStatus = 'error'
        state.reconnectAttempts += 1
        state.error = {
          type: 'websocket_connection_error',
          message: 'Failed to establish real-time connection',
          recovery_suggestions: ['Check your internet connection', 'Try refreshing the page']
        }
      })
      
      // WebSocket disconnection
      .addCase(disconnectWebSocket.fulfilled, (state) => {
        state.connectionStatus = 'disconnected'
        state.currentAgent = null
        state.isTyping = false
      })
      
      .addCase(disconnectWebSocket.rejected, (state, action) => {
        state.error = action.payload as EnhancedError
      })
  }
})

export const {
  addMessage,
  updateMessage,
  removeMessage,
  clearMessages,
  setSessionId,
  setUserId,
  resetSession,
  setSelectedPackage,
  updatePackage,
  setLoading,
  setTyping,
  setConversationMode,
  setGuidedFlow,
  setError,
  clearError,
  addWarning,
  removeWarning,
  clearWarnings,
  addAgentDecision,
  setCurrentAgent,
  updateEnhancedFeatures,
  updateCacheStats,
  setConnectionStatus,
  setReconnectAttempts,
  setRealTimeUpdatesEnabled,
  handleWorkflowStatusUpdate,
  handleAgentExecutionUpdate,
  handleTypingIndicatorUpdate,
  handleRecommendationUpdate
} = enhancedConversationSlice.actions

export const { actions } = enhancedConversationSlice
export default enhancedConversationSlice.reducer