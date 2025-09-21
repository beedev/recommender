/**
 * Sparky AI Assistant Service
 * Service layer for integration with the Sparky AI backend
 */

import { api } from '../api/apiClient'
import { API_ENDPOINTS } from '../api/endpoints'

// Request/Response types matching backend Pydantic models
export interface SparkyConversationRequest {
  message: string
  user_id?: string
  session_id?: string
  language?: string
}

export interface WeldingRequirement {
  process: string[]
  material?: string
  current?: number
  voltage?: number
  thickness?: number
  environment?: string
  application?: string
}

export interface SparkyPackageRecommendation {
  package_id: string
  powersource: Record<string, any>
  feeder?: Record<string, any>
  cooler?: Record<string, any>
  torch?: Record<string, any>
  accessories: Record<string, any>[]
  total_price?: number
  compatibility_confidence: number
  recommendation_reason: string
  sales_evidence: string
}

export interface SparkyConversationResponse {
  response: string
  requirements?: WeldingRequirement
  packages: SparkyPackageRecommendation[]
  conversation_id: string
  language: string
  confidence: number
  response_time_ms: number
}

export class SparkyService {
  private cache = new Map<string, { data: any; timestamp: number }>()
  private readonly CACHE_TTL = 5 * 60 * 1000 // 5 minutes
  private requestCount = 0
  private cacheHits = 0

  /**
   * Send a message to Sparky AI assistant
   */
  async chat(request: SparkyConversationRequest): Promise<SparkyConversationResponse> {
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
      const response = await api.post<SparkyConversationResponse>(
        API_ENDPOINTS.SPARKY.CHAT,
        {
          message: request.message,
          user_id: request.user_id || 'anonymous',
          session_id: request.session_id,
          language: request.language || 'en'
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
   * Get Sparky service status
   */
  async getStatus(): Promise<any> {
    try {
      return await api.get(API_ENDPOINTS.SPARKY.STATUS)
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Get supported languages
   */
  async getLanguages(): Promise<any> {
    try {
      return await api.get(API_ENDPOINTS.SPARKY.LANGUAGES)
    } catch (error: any) {
      throw this.handleServiceError(error)
    }
  }

  /**
   * Safe wrapper for chat method with error handling
   */
  async chatSafe(request: SparkyConversationRequest): Promise<SparkyConversationResponse> {
    try {
      return await this.chat(request)
    } catch (error: any) {
      // Fallback response for UI consistency
      return {
        response: "I'm having trouble right now. Please try again in a moment.",
        packages: [],
        conversation_id: request.session_id || `fallback-${Date.now()}`,
        language: request.language || 'en',
        confidence: 0.0,
        response_time_ms: 0
      }
    }
  }

  // Private helper methods
  private validateRequest(request: SparkyConversationRequest): void {
    if (!request.message || request.message.trim().length === 0) {
      throw new Error('Message is required')
    }
    if (request.message.length > 2000) {
      throw new Error('Message too long (max 2000 characters)')
    }
  }

  private generateCacheKey(request: SparkyConversationRequest): string {
    const keyData = {
      message: request.message,
      user_id: request.user_id,
      language: request.language
    }
    return `sparky:${btoa(JSON.stringify(keyData))}`
  }

  private getFromCache(key: string): SparkyConversationResponse | null {
    const cached = this.cache.get(key)
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      return cached.data
    }
    return null
  }

  private setCache(key: string, data: SparkyConversationResponse): void {
    this.cache.set(key, { data, timestamp: Date.now() })
  }

  private handleServiceError(error: any): Error {
    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      
      // Handle specific Sparky error types
      if (status === 400) {
        return new Error(data.detail?.message || 'Invalid request')
      }
      if (status === 500) {
        return new Error(data.detail?.message || 'Sparky service error')
      }
      if (status === 503) {
        return new Error('Sparky service is temporarily unavailable')
      }
      
      return new Error(`Sparky service error: ${status}`)
    }
    
    if (error.request) {
      return new Error('Unable to reach Sparky service')
    }
    
    return new Error(error.message || 'Unknown Sparky service error')
  }

  // Performance metrics
  getMetrics() {
    return {
      requestCount: this.requestCount,
      cacheHits: this.cacheHits,
      cacheHitRate: this.requestCount > 0 ? (this.cacheHits / this.requestCount) * 100 : 0
    }
  }
}

// Export singleton instance
export const sparkyService = new SparkyService()
export default sparkyService