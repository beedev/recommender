/**
 * Observability Panel Component
 * Displays LangSmith traces, performance metrics, and agent decision timeline
 */

import React, { useState, useEffect } from 'react'
import Card from '@components/common/Card'
import Button from '@components/common/Button'
import LoadingSpinner from '@components/common/LoadingSpinner'
import Badge from '@components/common/Badge'
import { enhancedOrchestratorService } from '@services/enhanced-orchestrator/enhancedOrchestratorService'
import {
  LangSmithTraceData,
  PerformanceDashboardData,
  AgentDecisionTimeline,
  CostTrackingData
} from '../../../types/enhanced-orchestrator'

interface ObservabilityPanelProps {
  sessionId: string
  isVisible: boolean
  onClose: () => void
}

type TabType = 'traces' | 'performance' | 'decisions' | 'costs'

export const ObservabilityPanel: React.FC<ObservabilityPanelProps> = ({
  sessionId,
  isVisible,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('traces')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Data states
  const [traceData, setTraceData] = useState<LangSmithTraceData | null>(null)
  const [performanceData, setPerformanceData] = useState<PerformanceDashboardData | null>(null)
  const [decisionTimeline, setDecisionTimeline] = useState<AgentDecisionTimeline | null>(null)
  const [costData, setCostData] = useState<CostTrackingData | null>(null)
  
  // LangGraph tracing control
  const [tracingEnabled, setTracingEnabled] = useState(true)

  /**
   * Load data based on active tab
   */
  const loadData = async (tab: TabType) => {
    setLoading(true)
    setError(null)

    try {
      switch (tab) {
        case 'traces':
          const traces = await enhancedOrchestratorService.getLangSmithTraces(sessionId, 50)
          setTraceData(traces)
          break
          
        case 'performance':
          const performance = await enhancedOrchestratorService.getPerformanceDashboard('1h', true, true)
          setPerformanceData(performance)
          break
          
        case 'decisions':
          const timeline = await enhancedOrchestratorService.getAgentDecisionTimeline(sessionId)
          setDecisionTimeline(timeline)
          break
          
        case 'costs':
          const costs = await enhancedOrchestratorService.getCostTrackingData(sessionId)
          setCostData(costs)
          break
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load observability data')
    } finally {
      setLoading(false)
    }
  }

  /**
   * Toggle LangGraph tracing
   */
  const toggleTracing = async () => {
    try {
      await enhancedOrchestratorService.enableLangGraphTracing(!tracingEnabled)
      setTracingEnabled(!tracingEnabled)
    } catch (err: any) {
      setError(err.message || 'Failed to toggle tracing')
    }
  }

  // Load data when tab changes or component becomes visible
  useEffect(() => {
    if (isVisible) {
      loadData(activeTab)
    }
  }, [activeTab, isVisible, sessionId])

  if (!isVisible) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-6xl h-5/6 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Observability Dashboard
            </h2>
            <Badge variant="secondary">Session: {sessionId.slice(-8)}</Badge>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={toggleTracing}
              className={tracingEnabled ? 'text-green-600' : 'text-gray-600'}
            >
              {tracingEnabled ? 'Tracing ON' : 'Tracing OFF'}
            </Button>
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-gray-200">
          {[
            { key: 'traces', label: 'LangSmith Traces', icon: '🔍' },
            { key: 'performance', label: 'Performance', icon: '📊' },
            { key: 'decisions', label: 'Agent Timeline', icon: '🤖' },
            { key: 'costs', label: 'Cost Tracking', icon: '💰' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as TabType)}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-auto p-6">
          {loading && (
            <div className="flex items-center justify-center h-64">
              <LoadingSpinner size="lg" />
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex">
                <div className="text-red-400">⚠️</div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">Error</h3>
                  <p className="mt-1 text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {!loading && !error && (
            <>
              {activeTab === 'traces' && <TracesView data={traceData} />}
              {activeTab === 'performance' && <PerformanceView data={performanceData} />}
              {activeTab === 'decisions' && <DecisionTimelineView data={decisionTimeline} />}
              {activeTab === 'costs' && <CostTrackingView data={costData} />}
            </>
          )}
        </div>
      </Card>
    </div>
  )
}

/**
 * LangSmith Traces View
 */
const TracesView: React.FC<{ data: LangSmithTraceData | null }> = ({ data }) => {
  if (!data) return <div>No trace data available</div>

  return (
    <div className="space-y-4">
      {/* LangSmith Status */}
      <Card className="p-4">
        <h3 className="text-lg font-medium mb-3">LangSmith Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-500">Available</div>
            <div className={`font-medium ${data.langsmith_status.available ? 'text-green-600' : 'text-red-600'}`}>
              {data.langsmith_status.available ? 'Yes' : 'No'}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Active Traces</div>
            <div className="font-medium">{data.langsmith_status.active_traces}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Project</div>
            <div className="font-medium">{data.langsmith_status.project}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Tracing Enabled</div>
            <div className={`font-medium ${data.langsmith_status.tracing_enabled ? 'text-green-600' : 'text-red-600'}`}>
              {data.langsmith_status.tracing_enabled ? 'Yes' : 'No'}
            </div>
          </div>
        </div>
      </Card>

      {/* Traces List */}
      <Card className="p-4">
        <h3 className="text-lg font-medium mb-3">
          Traces ({data.trace_data.total_traces})
        </h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {data.trace_data.traces.map((trace, index) => (
            <div key={index} className="border border-gray-200 rounded-md p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{trace.operation}</div>
                  <div className="text-sm text-gray-500">
                    ID: {trace.trace_id.slice(0, 8)}...
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">
                    {new Date(trace.start_time).toLocaleTimeString()}
                  </div>
                  {trace.langsmith_run_id && (
                    <div className="text-xs text-blue-600">
                      Run: {trace.langsmith_run_id.slice(0, 8)}...
                    </div>
                  )}
                </div>
              </div>
              {trace.metadata && Object.keys(trace.metadata).length > 0 && (
                <div className="mt-2 text-xs text-gray-600">
                  <pre className="bg-gray-50 p-2 rounded overflow-x-auto">
                    {JSON.stringify(trace.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

/**
 * Performance View
 */
const PerformanceView: React.FC<{ data: PerformanceDashboardData | null }> = ({ data }) => {
  if (!data) return <div>No performance data available</div>

  return (
    <div className="space-y-4">
      {/* Overview */}
      <Card className="p-4">
        <h3 className="text-lg font-medium mb-3">Service Overview</h3>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <div className="text-sm text-gray-500">Status</div>
            <div className={`font-medium ${
              data.overview.service_status === 'healthy' ? 'text-green-600' : 'text-red-600'
            }`}>
              {data.overview.service_status}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Total Requests</div>
            <div className="font-medium">{data.overview.total_requests.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Success Rate</div>
            <div className="font-medium text-green-600">
              {(data.overview.success_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Avg Response Time</div>
            <div className="font-medium">{data.overview.average_response_time}ms</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Active Sessions</div>
            <div className="font-medium">{data.overview.active_sessions}</div>
          </div>
        </div>
      </Card>

      {/* Agent Performance */}
      {data.agents && (
        <Card className="p-4">
          <h3 className="text-lg font-medium mb-3">Agent Performance</h3>
          <div className="space-y-3">
            {Object.entries(data.agents.execution_counts).map(([agent, count]) => (
              <div key={agent} className="flex items-center justify-between">
                <div className="font-medium">{agent}</div>
                <div className="flex items-center space-x-4">
                  <div className="text-sm text-gray-500">
                    {count} executions
                  </div>
                  <div className="text-sm text-green-600">
                    {((1 - (data.agents!.error_rates[agent] || 0)) * 100).toFixed(1)}% success
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Flow Performance */}
      {data.flows && (
        <Card className="p-4">
          <h3 className="text-lg font-medium mb-3">Flow Performance</h3>
          <div className="space-y-3">
            {Object.entries(data.flows.state_counts).map(([state, count]) => (
              <div key={state} className="flex items-center justify-between">
                <div className="font-medium">{state}</div>
                <div className="text-sm text-gray-500">{count} transitions</div>
              </div>
            ))}
            <div className="pt-2 border-t">
              <div className="flex items-center justify-between">
                <div className="font-medium">Transition Success Rate</div>
                <div className="text-sm text-green-600">
                  {(data.flows.transition_success_rate * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}

/**
 * Agent Decision Timeline View
 */
const DecisionTimelineView: React.FC<{ data: AgentDecisionTimeline | null }> = ({ data }) => {
  if (!data) return <div>No decision timeline available</div>

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <h3 className="text-lg font-medium mb-3">
          Agent Decision Timeline ({data.timeline.length} events)
        </h3>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {data.timeline.map((event, index) => (
            <div key={index} className="border-l-4 border-blue-200 pl-4 pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Badge variant={event.event_type === 'error' ? 'destructive' : 'secondary'}>
                    {event.event_type}
                  </Badge>
                  {event.agent_name && (
                    <span className="font-medium">{event.agent_name}</span>
                  )}
                </div>
                <div className="text-sm text-gray-500">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </div>
              </div>
              
              {event.flow_state && (
                <div className="text-sm text-gray-600 mt-1">
                  Flow State: {event.flow_state}
                </div>
              )}
              
              {event.reasoning && (
                <div className="text-sm text-gray-700 mt-2">
                  {event.reasoning}
                </div>
              )}
              
              {event.confidence && (
                <div className="text-sm text-gray-500 mt-1">
                  Confidence: {(event.confidence * 100).toFixed(1)}%
                </div>
              )}
              
              {event.processing_time_ms && (
                <div className="text-sm text-gray-500 mt-1">
                  Processing Time: {event.processing_time_ms}ms
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

/**
 * Cost Tracking View
 */
const CostTrackingView: React.FC<{ data: CostTrackingData | null }> = ({ data }) => {
  if (!data) return <div>No cost data available</div>

  return (
    <div className="space-y-4">
      {/* Cost Overview */}
      <Card className="p-4">
        <h3 className="text-lg font-medium mb-3">Cost Overview</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-sm text-gray-500">Total Cost</div>
            <div className="font-medium text-lg">${data.cost_data.total_cost.toFixed(4)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Total Tokens</div>
            <div className="font-medium">{data.cost_data.token_usage.total_tokens.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Input Tokens</div>
            <div className="font-medium">{data.cost_data.token_usage.input_tokens.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-sm text-gray-500">Output Tokens</div>
            <div className="font-medium">{data.cost_data.token_usage.output_tokens.toLocaleString()}</div>
          </div>
        </div>
      </Card>

      {/* Cost by Model */}
      <Card className="p-4">
        <h3 className="text-lg font-medium mb-3">Cost by Model</h3>
        <div className="space-y-2">
          {Object.entries(data.cost_data.cost_by_model).map(([model, cost]) => (
            <div key={model} className="flex items-center justify-between">
              <div className="font-medium">{model}</div>
              <div className="text-sm">${cost.toFixed(4)}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Cost by Agent */}
      <Card className="p-4">
        <h3 className="text-lg font-medium mb-3">Cost by Agent</h3>
        <div className="space-y-2">
          {Object.entries(data.cost_data.cost_by_agent).map(([agent, cost]) => (
            <div key={agent} className="flex items-center justify-between">
              <div className="font-medium">{agent}</div>
              <div className="text-sm">${cost.toFixed(4)}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Session Costs */}
      {data.cost_data.session_costs.length > 0 && (
        <Card className="p-4">
          <h3 className="text-lg font-medium mb-3">Recent Session Costs</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {data.cost_data.session_costs.map((session, index) => (
              <div key={index} className="flex items-center justify-between text-sm">
                <div>
                  <div className="font-medium">{session.session_id.slice(-8)}...</div>
                  <div className="text-gray-500">
                    {new Date(session.timestamp).toLocaleString()}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium">${session.cost.toFixed(4)}</div>
                  <div className="text-gray-500">{session.token_count} tokens</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

export default ObservabilityPanel