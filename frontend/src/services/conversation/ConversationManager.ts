import { EnhancedOrchestratorService } from '../enhanced-orchestrator/enhancedOrchestratorService'
import { 
  EnhancedChatMessage, 
  EnhancedOrchestratorRequest,
  EnhancedOrchestratorResponse,
  ConversationContext,
  WeldingRequirements
} from '../../types/enhanced-orchestrator'

export interface ConversationManagerConfig {
  userId: string
  language?: string
  enableObservability?: boolean
}

export interface SparkyResponse {
  message: string
  mode: 'guided' | 'expert'
  packages?: any[]
  followUpQuestions?: string[]
  confidence: number
  sessionId: string
  metadata?: {
    processingTimeMs?: number
    agentDecisions?: any[]
    validationScore?: number
    recommendationConfidence?: number
  }
}

export class ConversationManager {
  private orchestratorService: EnhancedOrchestratorService
  private config: ConversationManagerConfig
  private conversationHistory: EnhancedChatMessage[] = []
  private currentContext: ConversationContext | null = null
  private sessionId: string | null = null

  constructor(config: ConversationManagerConfig) {
    this.config = config
    this.orchestratorService = new EnhancedOrchestratorService()
  }

  /**
   * Send a message and get Sparky's response
   */
  async sendMessage(message: string, options?: {
    flowType?: 'quick_package' | 'guided_flow'
    sessionId?: string
  }): Promise<SparkyResponse> {
    try {
      // Detect conversation mode based on message specificity
      const detectedMode = this.detectConversationMode(message)
      const flowType = options?.flowType || (detectedMode === 'expert' ? 'quick_package' : 'guided_flow')

      // Create user message
      const userMessage: EnhancedChatMessage = {
        id: `user-${Date.now()}`,
        content: message,
        sender: 'user',
        timestamp: new Date().toISOString(),
        metadata: {
          mode: detectedMode
        }
      }

      // Add to conversation history
      this.conversationHistory.push(userMessage)

      // Prepare API request
      const request: EnhancedOrchestratorRequest = {
        message,
        user_id: this.config.userId,
        session_id: options?.sessionId || this.sessionId || '',
        language: this.config.language || 'en',
        flow_type: flowType,
        context: this.currentContext as any || undefined,
        enable_observability: this.config.enableObservability || false
      }

      // Call enhanced orchestrator
      const response = await this.orchestratorService.processRecommendationRequest(request)

      // Update session ID
      this.sessionId = response.session_id

      // Create Sparky response message
      const sparkyMessage: EnhancedChatMessage = {
        id: `sparky-${Date.now()}`,
        content: this.extractResponseMessage(response),
        sender: 'sparky',
        timestamp: response.timestamp,
        metadata: {
          confidence: response.metadata.recommendation_confidence,
          mode: detectedMode,
          processingTime: response.processing_time_ms
        }
      }

      // Add to conversation history
      this.conversationHistory.push(sparkyMessage)

      // Update conversation context
      this.updateConversationContext(response, detectedMode)

      // Return formatted response
      return {
        message: sparkyMessage.content,
        mode: detectedMode,
        packages: response.data.packages || [],
        followUpQuestions: this.extractFollowUpQuestions(response),
        confidence: response.metadata.recommendation_confidence,
        sessionId: response.session_id,
        metadata: {
          processingTimeMs: response.processing_time_ms,
          agentDecisions: [], // TODO: Extract from response when available
          validationScore: response.metadata.validation_score,
          recommendationConfidence: response.metadata.recommendation_confidence
        }
      }

    } catch (error) {
      console.error('ConversationManager error:', error)
      
      // Create error response
      const errorMessage: EnhancedChatMessage = {
        id: `error-${Date.now()}`,
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
        sender: 'sparky',
        timestamp: new Date().toISOString(),
        metadata: {
          confidence: 0,
          mode: 'expert',
          error: true
        }
      }

      this.conversationHistory.push(errorMessage)

      return {
        message: errorMessage.content,
        mode: 'expert',
        packages: [],
        followUpQuestions: [],
        confidence: 0,
        sessionId: this.sessionId || 'error-session'
      }
    }
  }

  /**
   * Detect conversation mode based on message content
   */
  private detectConversationMode(message: string): 'guided' | 'expert' {
    const lowerMessage = message.toLowerCase()
    
    // Expert mode indicators - specific technical terms and requirements
    const expertIndicators = [
      // Specific amperage/voltage
      /\d+\s*a\b|\d+\s*amp/,
      /\d+\s*v\b|\d+\s*volt/,
      
      // Specific processes
      /mig|tig|stick|mma|fcaw|gmaw|gtaw/,
      
      // Specific materials
      /aluminum|steel|stainless|carbon/,
      
      // Specific features
      /water.?cool|air.?cool|pulse|synergic/,
      
      // Model numbers or specific requirements
      /\d{3,4}[a-z]?/,
      
      // Multiple specific requirements in one message
      /\band\b.*\band\b.*\band\b/
    ]

    // Guided mode indicators - general or vague requests
    const guidedIndicators = [
      /need.*welding|want.*weld|looking.*weld/,
      /beginner|new.*weld|start.*weld/,
      /recommend|suggest|help.*choose/,
      /what.*best|which.*should/,
      /don't know|not sure|help.*decide/
    ]

    // Count expert indicators
    const expertScore = expertIndicators.reduce((score, pattern) => {
      return score + (pattern.test(lowerMessage) ? 1 : 0)
    }, 0)

    // Count guided indicators
    const guidedScore = guidedIndicators.reduce((score, pattern) => {
      return score + (pattern.test(lowerMessage) ? 1 : 0)
    }, 0)

    // Decision logic
    if (expertScore >= 2) return 'expert'
    if (guidedScore > 0 && expertScore === 0) return 'guided'
    if (message.length > 50 && expertScore > 0) return 'expert'
    if (message.length < 20) return 'guided'

    // Default to guided for ambiguous cases
    return 'guided'
  }

  /**
   * Extract the main response message from API response
   */
  private extractResponseMessage(response: EnhancedOrchestratorResponse): string {
    // If we have packages, create a response about them
    if (response.data.packages && response.data.packages.length > 0) {
      const packageCount = response.data.packages.length
      return `I found ${packageCount} welding package${packageCount > 1 ? 's' : ''} that match your requirements. Take a look at the recommendations on the right!`
    }

    // If we have step-by-step options (guided mode)
    if (response.data.step_by_step_options) {
      return this.formatGuidedResponse(response.data.step_by_step_options)
    }

    // Default response based on current step
    if (response.data.current_step) {
      return this.formatStepResponse(response.data.current_step)
    }

    // Fallback response
    return 'I\'m here to help you find the right welding equipment. Could you tell me more about what you need?'
  }

  /**
   * Format guided mode response with questions
   */
  private formatGuidedResponse(stepOptions: any): string {
    if (stepOptions.question) {
      return stepOptions.question
    }

    if (stepOptions.options && Array.isArray(stepOptions.options)) {
      const optionsList = stepOptions.options.map((opt: any, index: number) => 
        `${index + 1}. ${opt.label || opt.name || opt}`
      ).join('\n')
      
      return `Please choose from the following options:\n\n${optionsList}`
    }

    return 'Let me help you step by step. What type of welding will you be doing?'
  }

  /**
   * Format response based on current workflow step
   */
  private formatStepResponse(currentStep: string): string {
    const stepResponses: Record<string, string> = {
      'initialization': 'Let me understand your welding requirements...',
      'translation': 'Processing your request...',
      'compatibility': 'Checking compatible equipment...',
      'sales_analysis': 'Analyzing product recommendations...',
      'recommendation': 'Finding the best matches for you...',
      'package_building': 'Building complete welding packages...',
      'validation': 'Validating recommendations...',
      'service_communication': 'Preparing your results...'
    }

    return stepResponses[currentStep] || 'Processing your request...'
  }

  /**
   * Extract follow-up questions from response
   */
  private extractFollowUpQuestions(response: EnhancedOrchestratorResponse): string[] {
    const questions: string[] = []

    if (response.data.step_by_step_options?.follow_up_questions) {
      questions.push(...response.data.step_by_step_options.follow_up_questions)
    }

    return questions
  }

  /**
   * Update conversation context with new information
   */
  private updateConversationContext(response: EnhancedOrchestratorResponse, mode: 'guided' | 'expert'): void {
    this.currentContext = {
      sessionId: response.session_id,
      userId: this.config.userId,
      currentMode: mode,
      extractedRequirements: this.extractRequirements(response),
      conversationHistory: this.conversationHistory
    }
  }

  /**
   * Extract welding requirements from response
   */
  private extractRequirements(_response: EnhancedOrchestratorResponse): WeldingRequirements {
    // This would be populated by the backend analysis
    // For now, return empty requirements
    return {}
  }

  /**
   * Get conversation history
   */
  getConversationHistory(): EnhancedChatMessage[] {
    return [...this.conversationHistory]
  }

  /**
   * Reset conversation
   */
  resetConversation(): void {
    this.conversationHistory = []
    this.currentContext = null
    this.sessionId = null
  }

  /**
   * Update conversation context manually
   */
  updateContext(context: Partial<ConversationContext>): void {
    if (this.currentContext) {
      this.currentContext = { ...this.currentContext, ...context }
    }
  }

  /**
   * Get current session ID
   */
  getSessionId(): string | null {
    return this.sessionId
  }

  /**
   * Get current conversation mode
   */
  getCurrentMode(): 'guided' | 'expert' | null {
    return this.currentContext?.currentMode || null
  }
}

export default ConversationManager