/**
 * Performance Monitor Component
 * Real-time performance monitoring widget for enhanced orchestrator
 */

import React, { useState, useEffect } from 'react'
import Card from '@components/common/Card'
import Badge from '@components/common/Badge'
import { enhancedOrchestratorService } from '@services/enhanced-orchestrator/enhancedOrchestratorService'

interface PerformanceMonitorProps {
  sessionId?: string
  refreshInterval?: number
  compact?: boolean
}

interface PerformanceMetrics {
  responseTime: number
  successRate: number
  errorCount: number
  activeAgents: number
  cacheHitRate: number
  connectionStatus: 'healthy' | 'degraded' | 'unhealthy'
}

export const PerformanceMonitor: React.FC<PerformanceMonitorProps> = ({
  sessionId,
  refreshInterval = 30000, // 30 seconds
  compact = false
}) => {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  /**
   * Fetch performance metrics
   */
  const fetchMetrics = async () => {
    try {
      setError(null)
      
      // Get service status and performance data
      const [serviceStatus, performanceData] = await Promise.all([
        enhancedOrchestratorService.getServiceStatus(),
        enhancedOrchestratorService.getPerformanceDashboard('5m', true, true)
      ])

      // Extract metrics
      const newMetrics: PerformanceMetrics = {
        responseTime: performanceData.overview.average_response_time || 0,
        successRate: performanceData.overview.success_rate || 0,
        errorCount: performanceData.overview.total_requests - 
                   (performanceData.overview.total_requests * performanceData.overview.success_rate),
        activeAgents: Object.keys(performanceData.agents?.execution_counts || {}).length,
        cacheHitRate: enhancedOrchestratorService.getCacheStats().hitRate,
        connectionStatus: serviceStatus.health.orchestrator === 'healthy' ? 'healthy' :
                         serviceStatus.health.orchestrator === 'degraded' ? 'degraded' : 'unhealthy'
      }

      setMetrics(newMetrics)
      setLastUpdate(new Date())
      setLoading(false)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch performance metrics')
      setLoading(false)
    }
  }

  // Initial load and periodic refresh
  useEffect(() => {
    fetchMetrics()
    
    const interval = setInterval(fetchMetrics, refreshInterval)
    return () => clearInterval(interval)
  }, [refreshInterval])

  if (loading && !metrics) {
    return (
      <Card className={`p-4 ${compact ? 'text-sm' : ''}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-3/4"></div>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className={`p-4 ${compact ? 'text-sm' : ''}`}>
        <div className="text-red-600">
          <div className="font-medium">Performance Monitor Error</div>
          <div className="text-sm">{error}</div>
        </div>
      </Card>
    )
  }

  if (!metrics) return null

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600'
      case 'degraded': return 'text-yellow-600'
      case 'unhealthy': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'healthy': return 'success' as const
      case 'degraded': return 'warning' as const
      case 'unhealthy': return 'destructive' as const
      default: return 'secondary' as const
    }
  }

  if (compact) {
    return (
      <Card className="p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Badge variant={getStatusBadgeVariant(metrics.connectionStatus)}>
              {metrics.connectionStatus}
            </Badge>
            <span className="text-sm text-gray-600">
              {metrics.responseTime}ms
            </span>
          </div>
          <div className="text-xs text-gray-500">
            {lastUpdate?.toLocaleTimeString()}
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium">Performance Monitor</h3>
        <div className="flex items-center space-x-2">
          <Badge variant={getStatusBadgeVariant(metrics.connectionStatus)}>
            {metrics.connectionStatus}
          </Badge>
          {lastUpdate && (
            <span className="text-xs text-gray-500">
              Updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {/* Response Time */}
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {metrics.responseTime}ms
          </div>
          <div className="text-sm text-gray-500">Response Time</div>
        </div>

        {/* Success Rate */}
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {(metrics.successRate * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500">Success Rate</div>
        </div>

        {/* Error Count */}
        <div className="text-center">
          <div className={`text-2xl font-bold ${
            metrics.errorCount > 0 ? 'text-red-600' : 'text-gray-400'
          }`}>
            {Math.round(metrics.errorCount)}
          </div>
          <div className="text-sm text-gray-500">Errors (5min)</div>
        </div>

        {/* Active Agents */}
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {metrics.activeAgents}
          </div>
          <div className="text-sm text-gray-500">Active Agents</div>
        </div>

        {/* Cache Hit Rate */}
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {metrics.cacheHitRate.toFixed(1)}%
          </div>
          <div className="text-sm text-gray-500">Cache Hit Rate</div>
        </div>

        {/* Connection Status */}
        <div className="text-center">
          <div className={`text-2xl font-bold ${getStatusColor(metrics.connectionStatus)}`}>
            ●
          </div>
          <div className="text-sm text-gray-500">Connection</div>
        </div>
      </div>

      {/* Performance Indicators */}
      <div className="mt-4 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span>Response Time</span>
          <div className="flex items-center space-x-2">
            <div className="w-24 bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${
                  metrics.responseTime < 500 ? 'bg-green-500' :
                  metrics.responseTime < 1000 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ 
                  width: `${Math.min((metrics.responseTime / 2000) * 100, 100)}%` 
                }}
              />
            </div>
            <span className="text-xs text-gray-500">
              {metrics.responseTime < 500 ? 'Fast' :
               metrics.responseTime < 1000 ? 'Normal' : 'Slow'}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span>Success Rate</span>
          <div className="flex items-center space-x-2">
            <div className="w-24 bg-gray-200 rounded-full h-2">
              <div 
                className="h-2 bg-green-500 rounded-full"
                style={{ width: `${metrics.successRate * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-500">
              {metrics.successRate > 0.95 ? 'Excellent' :
               metrics.successRate > 0.9 ? 'Good' : 'Poor'}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between text-sm">
          <span>Cache Performance</span>
          <div className="flex items-center space-x-2">
            <div className="w-24 bg-gray-200 rounded-full h-2">
              <div 
                className="h-2 bg-blue-500 rounded-full"
                style={{ width: `${metrics.cacheHitRate}%` }}
              />
            </div>
            <span className="text-xs text-gray-500">
              {metrics.cacheHitRate > 80 ? 'Excellent' :
               metrics.cacheHitRate > 60 ? 'Good' : 'Poor'}
            </span>
          </div>
        </div>
      </div>

      {/* Refresh Button */}
      <div className="mt-4 flex justify-center">
        <button
          onClick={fetchMetrics}
          disabled={loading}
          className="text-sm text-blue-600 hover:text-blue-800 disabled:text-gray-400"
        >
          {loading ? 'Refreshing...' : 'Refresh Now'}
        </button>
      </div>
    </Card>
  )
}

export default PerformanceMonitor