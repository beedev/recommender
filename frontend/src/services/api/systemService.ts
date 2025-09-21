import { api } from './client'

export interface SystemService {
  service: string
  status: 'online' | 'offline' | 'warning'
  response_time_ms: number
  details: string[]
}

export interface SystemHealthResponse {
  timestamp: string
  services: SystemService[]
}

export interface PerformanceMetrics {
  cpu_usage: number
  memory_usage: number
  memory_used_gb: number
  memory_total_gb: number
  disk_usage: number
  disk_used_gb: number
  disk_total_gb: number
  network_sent_mb: number
  network_recv_mb: number
}

export interface PerformanceResponse {
  timestamp: string
  metrics: PerformanceMetrics
}

export interface DatabaseMetrics {
  neo4j: {
    total_nodes: number
    total_relationships: number
    products: number
    packages: number
    status: string
  }
  postgresql: {
    database_size: string
    table_count: number
    pool_size: string
    version: string
    status: string
  }
}

export interface DatabaseResponse {
  timestamp: string
  neo4j: DatabaseMetrics['neo4j']
  postgresql: DatabaseMetrics['postgresql']
}

export interface AIMetrics {
  openai: {
    api_configured: boolean
    model: string
    temperature: number
    max_tokens: number
    timeout_seconds: number
    max_retries: number
  }
  langsmith: {
    api_configured: boolean
    project: string
    tracing_enabled: boolean
  }
  note: string
}

export interface AIResponse {
  timestamp: string
  openai: AIMetrics['openai']
  langsmith: AIMetrics['langsmith']
  note: string
}

export interface SystemActivity {
  id: string
  type: string
  message: string
  timestamp: string
  status: 'success' | 'warning' | 'error'
  details: any
}

export interface ActivityResponse {
  timestamp: string
  activities: SystemActivity[]
  total_count: number
}

export const systemService = {
  /**
   * Get system health status for all services
   */
  getSystemHealth: (): Promise<SystemHealthResponse> => {
    return api.get<SystemHealthResponse>('/v1/system/health')
  },

  /**
   * Get real-time performance metrics
   */
  getPerformanceMetrics: (): Promise<PerformanceResponse> => {
    return api.get<PerformanceResponse>('/v1/system/metrics/performance')
  },

  /**
   * Get database metrics and statistics
   */
  getDatabaseMetrics: (): Promise<DatabaseResponse> => {
    return api.get<DatabaseResponse>('/v1/system/metrics/database')
  },

  /**
   * Get AI model usage metrics
   */
  getAIMetrics: (): Promise<AIResponse> => {
    return api.get<AIResponse>('/v1/system/metrics/ai')
  },

  /**
   * Get system activity log
   */
  getSystemActivity: (): Promise<ActivityResponse> => {
    return api.get<ActivityResponse>('/v1/system/activity')
  }
}