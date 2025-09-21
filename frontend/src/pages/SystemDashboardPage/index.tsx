import React, { useEffect, useState } from 'react'
// import { useTranslation } from 'react-i18next'
import { 
  Database, 
  Activity,
  Zap,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { systemService, SystemService, PerformanceMetrics, DatabaseMetrics, AIMetrics, SystemActivity } from '@services/api/systemService'

// interface MetricData {
//   label: string
//   value: string | number
//   trend?: 'up' | 'down' | 'stable'
// }

const SystemDashboardPage: React.FC = () => {
  // const { t } = useTranslation(['common']) // Commented out until used
  const [systemServices, setSystemServices] = useState<SystemService[]>([])
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null)
  const [databaseMetrics, setDatabaseMetrics] = useState<DatabaseMetrics | null>(null)
  const [aiMetrics, setAIMetrics] = useState<AIMetrics | null>(null)
  const [systemActivities, setSystemActivities] = useState<SystemActivity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSystemData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch all system data in parallel
      const [healthData, perfData, dbData, aiData, activityData] = await Promise.all([
        systemService.getSystemHealth(),
        systemService.getPerformanceMetrics(), 
        systemService.getDatabaseMetrics(),
        systemService.getAIMetrics(),
        systemService.getSystemActivity()
      ])

      setSystemServices(healthData.services)
      setPerformanceMetrics(perfData.metrics)
      setDatabaseMetrics({ neo4j: dbData.neo4j, postgresql: dbData.postgresql })
      setAIMetrics({ openai: aiData.openai, langsmith: aiData.langsmith, note: aiData.note })
      setSystemActivities(activityData.activities)

    } catch (err) {
      console.error('Failed to fetch system data:', err)
      setError('Failed to load system data. Please refresh the page.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSystemData()
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchSystemData, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (status: SystemService['status']) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="h-6 w-6 text-green-600" />
      case 'warning':
        return <AlertTriangle className="h-6 w-6 text-orange-600" />
      case 'offline':
        return <XCircle className="h-6 w-6 text-red-600" />
    }
  }

  const getStatusColor = (status: SystemService['status']) => {
    switch (status) {
      case 'online':
        return 'border-green-500'
      case 'warning':
        return 'border-orange-500'
      case 'offline':
        return 'border-red-500'
    }
  }

  const getStatusIndicator = (status: SystemService['status']) => {
    switch (status) {
      case 'online':
        return 'bg-green-500 shadow-green-500'
      case 'warning':
        return 'bg-orange-500 shadow-orange-500'
      case 'offline':
        return 'bg-red-500 shadow-red-500'
    }
  }

  if (loading) {
    return (
      <div className="p-8 min-h-screen bg-gradient-to-br from-amber-900 via-orange-700 to-yellow-600">
        <h1 className="text-white text-4xl font-bold mb-8">System Dashboard</h1>
        <div className="flex items-center justify-center h-64">
          <div className="bg-white bg-opacity-95 rounded-xl p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading system data...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 min-h-screen bg-gradient-to-br from-amber-900 via-orange-700 to-yellow-600">
        <h1 className="text-white text-4xl font-bold mb-8">System Dashboard</h1>
        <div className="flex items-center justify-center h-64">
          <div className="bg-white bg-opacity-95 rounded-xl p-8 text-center">
            <XCircle className="h-8 w-8 text-red-600 mx-auto mb-4" />
            <p className="text-red-600 font-medium">{error}</p>
            <button 
              onClick={fetchSystemData}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 min-h-screen bg-gradient-to-br from-amber-900 via-orange-700 to-yellow-600">
      <h1 className="text-white text-4xl font-bold mb-8">System Dashboard</h1>
      
      {/* System Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {systemServices.map((system, index) => (
          <div 
            key={index}
            className={`bg-white bg-opacity-95 rounded-xl p-6 border-2 ${getStatusColor(system.status)} transition-all hover:shadow-lg`}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-lg text-gray-900">{system.service}</h3>
              {getStatusIcon(system.status)}
            </div>
            <div className="flex items-center mb-2">
              <div className={`w-3 h-3 rounded-full mr-2 ${getStatusIndicator(system.status)} shadow-lg`}></div>
              <span className="font-medium capitalize text-gray-700">{system.status}</span>
            </div>
            <div className="text-sm text-gray-600 space-y-1">
              <p>Response: {system.response_time_ms}ms</p>
              {system.details.map((detail, idx) => (
                <p key={idx}>{detail}</p>
              ))}
            </div>
          </div>
        ))}
      </div>
      
      {/* Performance Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* System Performance */}
        <div className="bg-white bg-opacity-95 rounded-xl p-6 border border-yellow-400">
          <h3 className="font-bold text-xl mb-4 flex items-center gap-2 text-gray-900">
            <Activity className="h-5 w-5 text-blue-600" />
            System Performance
          </h3>
          {performanceMetrics && (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-700">CPU Usage</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${performanceMetrics.cpu_usage}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{performanceMetrics.cpu_usage}%</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Memory Usage</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${performanceMetrics.memory_usage}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{performanceMetrics.memory_usage}%</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Disk Usage</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-orange-600 h-2 rounded-full" 
                      style={{ width: `${performanceMetrics.disk_usage}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{performanceMetrics.disk_usage}%</span>
                </div>
              </div>
              <div className="pt-2 text-sm text-gray-600">
                <p>Memory: {performanceMetrics.memory_used_gb}GB / {performanceMetrics.memory_total_gb}GB</p>
                <p>Disk: {performanceMetrics.disk_used_gb}GB / {performanceMetrics.disk_total_gb}GB</p>
                <p>Network: ↑{performanceMetrics.network_sent_mb}MB ↓{performanceMetrics.network_recv_mb}MB</p>
              </div>
            </div>
          )}
        </div>
        
        {/* AI Model Performance */}
        <div className="bg-white bg-opacity-95 rounded-xl p-6 border border-yellow-400">
          <h3 className="font-bold text-xl mb-4 flex items-center gap-2 text-gray-900">
            <Zap className="h-5 w-5 text-purple-600" />
            AI Model Metrics
          </h3>
          {aiMetrics && (
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-700">OpenAI API</span>
                <span className="font-bold text-gray-900">
                  {aiMetrics.openai.api_configured ? 'Configured' : 'Missing'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">Model</span>
                <span className="font-bold text-gray-900">{aiMetrics.openai.model}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">Temperature</span>
                <span className="font-bold text-gray-900">{aiMetrics.openai.temperature}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">Max Tokens</span>
                <span className="font-bold text-gray-900">{aiMetrics.openai.max_tokens}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-700">LangSmith</span>
                <span className="font-bold text-gray-900">
                  {aiMetrics.langsmith.api_configured ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              {aiMetrics.note && (
                <div className="pt-2 text-xs text-gray-500 italic">
                  {aiMetrics.note}
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Database Stats */}
        <div className="bg-white bg-opacity-95 rounded-xl p-6 border border-yellow-400">
          <h3 className="font-bold text-xl mb-4 flex items-center gap-2 text-gray-900">
            <Database className="h-5 w-5 text-orange-600" />
            Database Stats
          </h3>
          {databaseMetrics && (
            <div className="space-y-3">
              <div className="mb-3">
                <h4 className="font-medium text-gray-800 mb-2">Neo4j Graph DB</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Nodes</span>
                    <span className="font-medium">{databaseMetrics.neo4j.total_nodes}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Relationships</span>
                    <span className="font-medium">{databaseMetrics.neo4j.total_relationships}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Products</span>
                    <span className="font-medium">{databaseMetrics.neo4j.products}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Packages</span>
                    <span className="font-medium">{databaseMetrics.neo4j.packages}</span>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-medium text-gray-800 mb-2">PostgreSQL</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Database Size</span>
                    <span className="font-medium">{databaseMetrics.postgresql.database_size}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tables</span>
                    <span className="font-medium">{databaseMetrics.postgresql.table_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Pool Size</span>
                    <span className="font-medium">{databaseMetrics.postgresql.pool_size}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Recent Activity */}
      <div className="bg-white bg-opacity-95 rounded-xl p-6 border border-yellow-400">
        <h3 className="font-bold text-xl mb-4 flex items-center gap-2 text-gray-900">
          <Clock className="h-5 w-5 text-indigo-600" />
          Recent System Activity
        </h3>
        {systemActivities && systemActivities.length > 0 ? (
          <div className="space-y-3">
            {systemActivities.map((activity) => (
              <div key={activity.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${
                    activity.status === 'success' ? 'bg-green-500' :
                    activity.status === 'warning' ? 'bg-orange-500' :
                    'bg-red-500'
                  }`}></div>
                  <span className="text-gray-800">{activity.message}</span>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(activity.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">No recent activity available</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default SystemDashboardPage