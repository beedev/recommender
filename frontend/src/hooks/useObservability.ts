/**
 * Observability Hook
 * Manages observability features including LangSmith traces, performance monitoring, and cost tracking
 */

import { useState, useEffect, useCallback } from 'react'
import { useAppSelector } from './redux'
import { enhancedOrchestratorService } from '@services/enhanced-orchestrator/enhancedOrchestratorService'
import {
  LangSmithTraceData,
  PerformanceDashboardData,
  AgentDecisionTimeline,
  CostTrackingData,
  LangGraphMetrics
} from '../types/enhanced-orchestrator'

export interface ObservabilityData {
  traces: LangSmithTraceData | null
  performance: PerformanceDashboardData | null
  decisions: AgentDecisionTimeline | null
  costs: CostTrackingData | null
  langGraphMetrics: LangGraphMetrics | null
}

export interface ObservabilityState {
  data: ObservabilityData
  loading: boolean
  error: string | null
  tracingEnabled: boolean
  lastUpdate: Date | null
}

export interface UseObservabilityOptions {
  sessionId?: string
  autoRefresh?: boolean
  refreshInterval?: number
  enableTracing?: boolean
}

export const useObservability = (options: UseObservabilityOptions = {}) => {
  const {
    sessionId,
    autoRefresh = false,
    refreshInterval = 30000, // 30 seconds
    enableTracing = true
  } = options

  const { sessionId: currentSessionId } = useAppSelector(state => state.enhancedConversation)
  const targetSessionId = sessionId || currentSessionId

  const [state, setState] = useState<ObservabilityState>({
    data: {
      traces: null,
      performance: null,
      decisions: null,
      costs: null,
      langGraphMetrics: null
    },
    loading: false,
    error: null,
    tracingEnabled: enableTracing,
    lastUpdate: null
  })

  /**
   * Load LangSmith traces
   */
  const loadTraces = useCallback(async (sessionFilter?: string, limit = 50) => {
    try {
      const traces = await enhancedOrchestratorService.getLangSmithTraces(
        sessionFilter || targetSessionId,
        limit
      )
      setState(prev => ({
        ...prev,
        data: { ...prev.data, traces },
        lastUpdate: new Date()
      }))
      return traces
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to load traces'
      }))
      throw error
    }
  }, [targetSessionId])

  /**
   * Load performance dashboard data
   */
  const loadPerformance = useCallback(async (timeWindow = '1h') => {
    try {
      const performance = await enhancedOrchestratorService.getPerformanceDashboard(
        timeWindow,
        true,
        true
      )
      setState(prev => ({
        ...prev,
        data: { ...prev.data, performance },
        lastUpdate: new Date()
      }))
      return performance
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to load performance data'
      }))
      throw error
    }
  }, [])

  /**
   * Load agent decision timeline
   */
  const loadDecisions = useCallback(async (sessionFilter?: string) => {
    if (!targetSessionId && !sessionFilter) return null

    try {
      const decisions = await enhancedOrchestratorService.getAgentDecisionTimeline(
        sessionFilter || targetSessionId!
      )
      setState(prev => ({
        ...prev,
        data: { ...prev.data, decisions },
        lastUpdate: new Date()
      }))
      return decisions
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to load decision timeline'
      }))
      throw error
    }
  }, [targetSessionId])

  /**
   * Load cost tracking data
   */
  const loadCosts = useCallback(async (sessionFilter?: string) => {
    try {
      const costs = await enhancedOrchestratorService.getCostTrackingData(
        sessionFilter || targetSessionId
      )
      setState(prev => ({
        ...prev,
        data: { ...prev.data, costs },
        lastUpdate: new Date()
      }))
      return costs
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to load cost data'
      }))
      throw error
    }
  }, [targetSessionId])

  /**
   * Load LangGraph metrics
   */
  const loadLangGraphMetrics = useCallback(async () => {
    try {
      const langGraphMetrics = await enhancedOrchestratorService.getLangGraphMetrics()
      setState(prev => ({
        ...prev,
        data: { ...prev.data, langGraphMetrics },
        lastUpdate: new Date()
      }))
      return langGraphMetrics
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to load LangGraph metrics'
      }))
      throw error
    }
  }, [])

  /**
   * Load all observability data
   */
  const loadAll = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      await Promise.allSettled([
        loadTraces(),
        loadPerformance(),
        loadDecisions(),
        loadCosts(),
        loadLangGraphMetrics()
      ])
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to load observability data'
      }))
    } finally {
      setState(prev => ({ ...prev, loading: false }))
    }
  }, [loadTraces, loadPerformance, loadDecisions, loadCosts, loadLangGraphMetrics])

  /**
   * Toggle LangGraph tracing
   */
  const toggleTracing = useCallback(async (enabled?: boolean) => {
    const newState = enabled !== undefined ? enabled : !state.tracingEnabled

    try {
      await enhancedOrchestratorService.enableLangGraphTracing(newState)
      setState(prev => ({
        ...prev,
        tracingEnabled: newState,
        lastUpdate: new Date()
      }))
      return newState
    } catch (error: any) {
      setState(prev => ({
        ...prev,
        error: error.message || 'Failed to toggle tracing'
      }))
      throw error
    }
  }, [state.tracingEnabled])

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  /**
   * Reset all data
   */
  const reset = useCallback(() => {
    setState({
      data: {
        traces: null,
        performance: null,
        decisions: null,
        costs: null,
        langGraphMetrics: null
      },
      loading: false,
      error: null,
      tracingEnabled: enableTracing,
      lastUpdate: null
    })
  }, [enableTracing])

  /**
   * Get observability summary
   */
  const getSummary = useCallback(() => {
    const { data } = state
    
    return {
      hasTraces: Boolean(data.traces?.trace_data.traces.length),
      traceCount: data.traces?.trace_data.total_traces || 0,
      hasPerformanceData: Boolean(data.performance),
      successRate: data.performance?.overview.success_rate || 0,
      responseTime: data.performance?.overview.average_response_time || 0,
      hasDecisions: Boolean(data.decisions?.timeline.length),
      decisionCount: data.decisions?.timeline.length || 0,
      hasCosts: Boolean(data.costs),
      totalCost: data.costs?.cost_data.total_cost || 0,
      langGraphAvailable: data.langGraphMetrics?.service_langgraph.available || false,
      tracingEnabled: state.tracingEnabled
    }
  }, [state])

  // Auto-refresh when enabled
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(loadAll, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, loadAll])

  // Load initial data when session changes
  useEffect(() => {
    if (targetSessionId) {
      loadAll()
    }
  }, [targetSessionId]) // eslint-disable-line react-hooks/exhaustive-deps

  return {
    // State
    ...state,
    
    // Data loaders
    loadTraces,
    loadPerformance,
    loadDecisions,
    loadCosts,
    loadLangGraphMetrics,
    loadAll,
    
    // Controls
    toggleTracing,
    clearError,
    reset,
    
    // Utilities
    getSummary,
    
    // Computed values
    hasData: Object.values(state.data).some(Boolean),
    isTracingAvailable: state.data.langGraphMetrics?.service_langgraph.available || false
  }
}

export default useObservability