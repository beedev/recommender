/**
 * Workflow Status Tracker Component
 * Displays real-time workflow status and agent flow states
 */

import React, { useState, useEffect } from 'react'
import Card from '@components/common/Card'
import Badge from '@components/common/Badge'
import LoadingSpinner from '@components/common/LoadingSpinner'
import { enhancedOrchestratorService } from '@services/enhanced-orchestrator/enhancedOrchestratorService'
import { useWebSocketIntegration } from '@hooks/useWebSocketIntegration'
import { WorkflowStatus } from '../../../types/enhanced-orchestrator'

interface WorkflowStatusTrackerProps {
  sessionId: string
  showDetails?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
}

const FLOW_STATES = [
  'initialization',
  'translation',
  'compatibility',
  'sales_analysis',
  'recommendation',
  'package_building',
  'validation',
  'service_communication',
  'completed'
]

export const WorkflowStatusTracker: React.FC<WorkflowStatusTrackerProps> = ({
  sessionId,
  showDetails = true,
  autoRefresh = true,
  refreshInterval = 5000
}) => {
  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  // WebSocket integration for real-time updates
  const { isConnected, requestWorkflowStatus } = useWebSocketIntegration({
    autoConnect: true
  })

  /**
   * Fetch workflow status
   */
  const fetchWorkflowStatus = async () => {
    try {
      setError(null)
      const status = await enhancedOrchestratorService.getWorkflowStatus(sessionId)
      setWorkflowStatus(status)
      setLastUpdate(new Date())
      setLoading(false)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch workflow status')
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    fetchWorkflowStatus()
  }, [sessionId])

  // Auto-refresh when not connected to WebSocket
  useEffect(() => {
    if (!autoRefresh || isConnected) return

    const interval = setInterval(fetchWorkflowStatus, refreshInterval)
    return () => clearInterval(interval)
  }, [autoRefresh, isConnected, refreshInterval])

  // Request status via WebSocket when connected
  useEffect(() => {
    if (isConnected && autoRefresh) {
      const interval = setInterval(requestWorkflowStatus, refreshInterval)
      return () => clearInterval(interval)
    }
  }, [isConnected, autoRefresh, refreshInterval, requestWorkflowStatus])

  /**
   * Get status badge variant
   */
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed': return 'success' as const
      case 'processing': return 'default' as const
      case 'error': return 'destructive' as const
      case 'cancelled': return 'secondary' as const
      default: return 'secondary' as const
    }
  }

  /**
   * Get flow state progress
   */
  const getFlowProgress = (currentState: string) => {
    const currentIndex = FLOW_STATES.indexOf(currentState)
    return currentIndex >= 0 ? ((currentIndex + 1) / FLOW_STATES.length) * 100 : 0
  }

  /**
   * Format duration
   */
  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
    return `${(ms / 60000).toFixed(1)}m`
  }

  if (loading && !workflowStatus) {
    return (
      <Card className="p-4">
        <div className="flex items-center space-x-2">
          <LoadingSpinner size="sm" />
          <span>Loading workflow status...</span>
        </div>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="p-4">
        <div className="text-red-600">
          <div className="font-medium">Workflow Status Error</div>
          <div className="text-sm">{error}</div>
        </div>
      </Card>
    )
  }

  if (!workflowStatus) return null

  const { workflow_state } = workflowStatus
  const progress = getFlowProgress(workflow_state.current_flow_state)

  return (
    <Card className="p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium">Workflow Status</h3>
        <div className="flex items-center space-x-2">
          <Badge variant={getStatusBadgeVariant(workflow_state.status)}>
            {workflow_state.status}
          </Badge>
          {isConnected && (
            <Badge variant="success" className="text-xs">
              Live
            </Badge>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between text-sm mb-2">
          <span>Progress</span>
          <span>{progress.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              workflow_state.status === 'completed' ? 'bg-green-500' :
              workflow_state.status === 'error' ? 'bg-red-500' :
              workflow_state.status === 'cancelled' ? 'bg-gray-500' :
              'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Current State */}
      <div className="mb-4">
        <div className="text-sm text-gray-500 mb-1">Current Flow State</div>
        <div className="font-medium text-lg capitalize">
          {workflow_state.current_flow_state.replace('_', ' ')}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="text-center">
          <div className="text-lg font-bold text-blue-600">
            {formatDuration(workflow_state.processing_time_ms)}
          </div>
          <div className="text-xs text-gray-500">Processing Time</div>
        </div>
        
        <div className="text-center">
          <div className="text-lg font-bold text-purple-600">
            {workflow_state.agent_count}
          </div>
          <div className="text-xs text-gray-500">Agents Used</div>
        </div>
        
        <div className="text-center">
          <div className={`text-lg font-bold ${
            workflow_state.error_count > 0 ? 'text-red-600' : 'text-gray-400'
          }`}>
            {workflow_state.error_count}
          </div>
          <div className="text-xs text-gray-500">Errors</div>
        </div>
        
        <div className="text-center">
          <div className={`text-lg font-bold ${
            workflow_state.warning_count > 0 ? 'text-yellow-600' : 'text-gray-400'
          }`}>
            {workflow_state.warning_count}
          </div>
          <div className="text-xs text-gray-500">Warnings</div>
        </div>
      </div>

      {/* Flow State Timeline */}
      {showDetails && (
        <div className="border-t pt-4">
          <div className="text-sm font-medium mb-3">Flow State Timeline</div>
          <div className="space-y-2">
            {FLOW_STATES.map((state, index) => {
              const isActive = state === workflow_state.current_flow_state
              const isCompleted = FLOW_STATES.indexOf(workflow_state.current_flow_state) > index
              const isPending = FLOW_STATES.indexOf(workflow_state.current_flow_state) < index

              return (
                <div key={state} className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    isActive ? 'bg-blue-500 animate-pulse' :
                    isCompleted ? 'bg-green-500' :
                    'bg-gray-300'
                  }`} />
                  <div className={`text-sm capitalize ${
                    isActive ? 'font-medium text-blue-600' :
                    isCompleted ? 'text-green-600' :
                    isPending ? 'text-gray-400' :
                    'text-gray-600'
                  }`}>
                    {state.replace('_', ' ')}
                  </div>
                  {isActive && (
                    <Badge variant="default" className="text-xs">
                      Current
                    </Badge>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Session Metrics */}
      {showDetails && workflowStatus.session_metrics && (
        <div className="border-t pt-4 mt-4">
          <div className="text-sm font-medium mb-3">Session Metrics</div>
          <div className="text-xs text-gray-600 space-y-1">
            {workflowStatus.session_metrics.executions && (
              <div>
                Executions: {workflowStatus.session_metrics.executions.length}
              </div>
            )}
            {workflowStatus.session_metrics.langgraph_checkpoints && (
              <div>
                LangGraph Checkpoints: {workflowStatus.session_metrics.langgraph_checkpoints.length}
              </div>
            )}
            {workflowStatus.session_metrics.performance_data && (
              <div>
                Performance Data Available: Yes
              </div>
            )}
          </div>
        </div>
      )}

      {/* Last Update */}
      <div className="border-t pt-2 mt-4">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Session: {sessionId.slice(-8)}...</span>
          {lastUpdate && (
            <span>Updated: {lastUpdate.toLocaleTimeString()}</span>
          )}
        </div>
      </div>
    </Card>
  )
}

export default WorkflowStatusTracker