/**
 * API Endpoints Configuration
 * Centralized endpoint definitions for the ESAB Welding Management System
 */

export const API_ENDPOINTS = {
  // Authentication endpoints
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    REGISTER: '/auth/register',
    FORGOT_PASSWORD: '/auth/forgot-password',
    RESET_PASSWORD: '/auth/reset-password',
    VERIFY_EMAIL: '/auth/verify-email',
    CHANGE_PASSWORD: '/auth/change-password',
    PROFILE: '/auth/profile',
  },


  // Enhanced Orchestrator endpoints
  ENHANCED_ORCHESTRATOR: {
    PROCESS: '/v1/orchestrator/process-enhanced',
    WORKFLOW_STATUS: (sessionId: string) => `/v1/orchestrator/workflow/${sessionId}/status`,
    WORKFLOW_CANCEL: (sessionId: string) => `/v1/orchestrator/workflow/${sessionId}/cancel`,
    WORKFLOW_CHECKPOINTS: (sessionId: string) => `/v1/orchestrator/workflow/checkpoint/${sessionId}`,
    SESSION_METRICS: (sessionId: string) => `/v1/orchestrator/session/${sessionId}/metrics`,
    LANGGRAPH_METRICS: '/v1/orchestrator/langgraph/metrics',
    LANGGRAPH_TRACING: '/v1/orchestrator/langgraph/tracing/enable',
    LANGSMITH_TRACES: '/v1/orchestrator/langsmith/traces',
    LANGSMITH_COSTS: '/v1/orchestrator/langsmith/costs',
    PERFORMANCE_DASHBOARD: '/v1/orchestrator/dashboard/performance',
    PERFORMANCE_METRICS: '/v1/orchestrator/metrics-enhanced',
    FLOW_VALIDATION: '/v1/orchestrator/flow-validation',
    SERVICE_STATUS: '/v1/orchestrator/status-enhanced',
    HEALTH_CHECK: '/v1/orchestrator/health-enhanced',
  },

  // Sparky AI Assistant endpoints
  SPARKY: {
    CHAT: '/api/v1/sparky/chat',
    CONTEXT: (userId: string, sessionId: string) => `/api/v1/sparky/context/${userId}/${sessionId}`,
    PREFERENCES: (userId: string, sessionId: string) => `/api/v1/sparky/context/${userId}/${sessionId}/preferences`,
    CLEAR_CONTEXT: (userId: string, sessionId: string) => `/api/v1/sparky/context/${userId}/${sessionId}`,
    LANGUAGES: '/api/v1/sparky/languages',
    STATUS: '/api/v1/sparky/status',
  },

  // Product and Inventory endpoints
  PRODUCTS: {
    LIST: '/products',
    DETAIL: (id: string) => `/products/${id}`,
    SEARCH: '/products/search',
    CATEGORIES: '/products/categories',
    BRANDS: '/products/brands',
    RECOMMENDATIONS: (id: string) => `/products/${id}/recommendations`,
    COMPARE: '/products/compare',
    REVIEWS: (id: string) => `/products/${id}/reviews`,
    SPECIFICATIONS: (id: string) => `/products/${id}/specifications`,
  },

  // Inventory management endpoints
  INVENTORY: {
    LIST: '/inventory',
    DETAIL: (id: string) => `/inventory/${id}`,
    UPDATE: (id: string) => `/inventory/${id}`,
    CREATE: '/inventory',
    DELETE: (id: string) => `/inventory/${id}`,
    STOCK_LEVELS: '/inventory/stock-levels',
    LOW_STOCK: '/inventory/low-stock',
    MOVEMENTS: '/inventory/movements',
    BULK_UPDATE: '/inventory/bulk-update',
  },

  // User management endpoints
  USERS: {
    LIST: '/users',
    DETAIL: (id: string) => `/users/${id}`,
    UPDATE: (id: string) => `/users/${id}`,
    CREATE: '/users',
    DELETE: (id: string) => `/users/${id}`,
    PREFERENCES: '/users/preferences',
    ACTIVITY: '/users/activity',
  },

  // Dashboard and analytics endpoints
  DASHBOARD: {
    STATS: '/dashboard/stats',
    CHARTS: '/dashboard/charts',
    RECENT_ACTIVITY: '/dashboard/recent-activity',
    ALERTS: '/dashboard/alerts',
    KPI: '/dashboard/kpi',
  },

  // File upload endpoints
  FILES: {
    UPLOAD: '/files/upload',
    DOWNLOAD: (id: string) => `/files/${id}/download`,
    DELETE: (id: string) => `/files/${id}`,
    LIST: '/files',
  },

  // Notification endpoints
  NOTIFICATIONS: {
    LIST: '/notifications',
    MARK_READ: (id: string) => `/notifications/${id}/read`,
    MARK_ALL_READ: '/notifications/read-all',
    DELETE: (id: string) => `/notifications/${id}`,
    PREFERENCES: '/notifications/preferences',
  },

  // System endpoints
  SYSTEM: {
    HEALTH: '/system/health',
    STATUS: '/system/status',
    VERSION: '/system/version',
    CONFIG: '/system/config',
  },

  // WebSocket endpoints
  WEBSOCKET: {
    CHAT: '/ws/chat',
    NOTIFICATIONS: '/ws/notifications',
    INVENTORY_UPDATES: '/ws/inventory',
    SYSTEM_STATUS: '/ws/status',
  },

  // Search endpoints
  SEARCH: {
    GLOBAL: '/search',
    PRODUCTS: '/search/products',
    USERS: '/search/users',
    HISTORY: '/search/history',
    SUGGESTIONS: '/search/suggestions',
  },

  // Reports endpoints
  REPORTS: {
    GENERATE: '/reports/generate',
    LIST: '/reports',
    DOWNLOAD: (id: string) => `/reports/${id}/download`,
    DELETE: (id: string) => `/reports/${id}`,
    TEMPLATES: '/reports/templates',
  },

  // Settings endpoints
  SETTINGS: {
    GENERAL: '/settings/general',
    SECURITY: '/settings/security',
    NOTIFICATIONS: '/settings/notifications',
    APPEARANCE: '/settings/appearance',
    INTEGRATIONS: '/settings/integrations',
    BACKUP: '/settings/backup',
  },
} as const

// Helper function to build URLs with query parameters
export const buildUrl = (endpoint: string, params?: Record<string, string | number | boolean>) => {
  if (!params) return endpoint

  const searchParams = new URLSearchParams()
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      searchParams.append(key, String(value))
    }
  })

  const queryString = searchParams.toString()
  return queryString ? `${endpoint}?${queryString}` : endpoint
}

// Helper function to replace path parameters
export const replacePathParams = (endpoint: string, params: Record<string, string>) => {
  let url = endpoint
  
  Object.entries(params).forEach(([key, value]) => {
    url = url.replace(`:${key}`, encodeURIComponent(value))
  })
  
  return url
}

// Type-safe endpoint builder
export const createEndpoint = {
  get: (endpoint: string, params?: Record<string, string | number | boolean>) => 
    buildUrl(endpoint, params),
  
  withParams: (endpoint: (params: any) => string, pathParams: any, queryParams?: Record<string, string | number | boolean>) => 
    buildUrl(endpoint(pathParams), queryParams),
}

export default API_ENDPOINTS