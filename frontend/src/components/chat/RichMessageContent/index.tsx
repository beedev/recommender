import React from 'react'
import { Package, Zap, AlertCircle, CheckCircle, Info, RefreshCw } from 'lucide-react'
import { EnhancedWeldingPackage } from '../../../types/enhanced-orchestrator'

export interface RichContent {
  type: 'package_tile' | 'error_recovery' | 'quick_actions' | 'info_card' | 'loading_status'
  data: any
}

interface RichMessageContentProps {
  content: RichContent
  onAction?: (action: string, data?: any) => void
  className?: string
}

export const RichMessageContent: React.FC<RichMessageContentProps> = ({
  content,
  onAction,
  className = ''
}) => {
  const renderContent = () => {
    switch (content.type) {
      case 'package_tile':
        return <PackageTile package={content.data} onAction={onAction} />
      
      case 'error_recovery':
        return <ErrorRecovery error={content.data} onAction={onAction} />
      
      case 'quick_actions':
        return <QuickActions actions={content.data} onAction={onAction} />
      
      case 'info_card':
        return <InfoCard info={content.data} onAction={onAction} />
      
      case 'loading_status':
        return <LoadingStatus status={content.data} />
      
      default:
        return null
    }
  }

  return (
    <div className={`rich-message-content ${className}`}>
      {renderContent()}
    </div>
  )
}

// Package Tile Component
const PackageTile: React.FC<{
  package: EnhancedWeldingPackage
  onAction?: ((action: string, data?: any) => void) | undefined
}> = ({ package: pkg, onAction }) => {
  const handleViewDetails = () => {
    onAction?.('view_package_details', pkg)
  }

  const handleSelectPackage = () => {
    onAction?.('select_package', pkg)
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Package className="w-5 h-5 text-sparky-gold" />
          <h4 className="font-semibold text-gray-900">{pkg.powersource.product_name}</h4>
        </div>
        <div className="text-sm text-green-600 font-medium">
          {(pkg.compatibility_confidence * 100).toFixed(0)}% Match
        </div>
      </div>
      
      <div className="space-y-2 mb-4">
        <div className="text-sm text-gray-600">
          <span className="font-medium">Power Source:</span> {pkg.powersource.description}
        </div>
        {pkg.feeder && (
          <div className="text-sm text-gray-600">
            <span className="font-medium">Feeder:</span> {pkg.feeder.description}
          </div>
        )}
        {pkg.cooler && (
          <div className="text-sm text-gray-600">
            <span className="font-medium">Cooler:</span> {pkg.cooler.description}
          </div>
        )}
      </div>
      
      <div className="flex items-center justify-between">
        <div className="text-lg font-bold text-gray-900">
          ${pkg.total_price?.toLocaleString() || 'Contact for pricing'}
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleViewDetails}
            className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 transition-colors"
          >
            Details
          </button>
          <button
            onClick={handleSelectPackage}
            className="px-3 py-1 text-sm bg-sparky-gold text-black rounded hover:bg-yellow-500 transition-colors"
          >
            Select
          </button>
        </div>
      </div>
    </div>
  )
}

// Error Recovery Component
const ErrorRecovery: React.FC<{
  error: {
    message: string
    suggestions: string[]
    canRetry: boolean
    retryAttempts?: number
  }
  onAction?: ((action: string, data?: any) => void) | undefined
}> = ({ error, onAction }) => {
  const handleRetry = () => {
    onAction?.('retry_message')
  }

  const handleReset = () => {
    onAction?.('reset_conversation')
  }

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <h4 className="font-medium text-red-800 mb-2">Something went wrong</h4>
          <p className="text-sm text-red-700 mb-3">{error.message}</p>
          
          {error.suggestions.length > 0 && (
            <div className="mb-3">
              <p className="text-sm font-medium text-red-800 mb-1">Try these solutions:</p>
              <ul className="text-sm text-red-700 space-y-1">
                {error.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-red-400">•</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="flex gap-2">
            {error.canRetry && (
              <button
                onClick={handleRetry}
                className="flex items-center gap-1 px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              >
                <RefreshCw className="w-3 h-3" />
                Retry {error.retryAttempts ? `(${error.retryAttempts})` : ''}
              </button>
            )}
            <button
              onClick={handleReset}
              className="px-3 py-1 text-sm border border-red-300 text-red-700 rounded hover:bg-red-100 transition-colors"
            >
              Start Over
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Quick Actions Component
const QuickActions: React.FC<{
  actions: Array<{
    label: string
    action: string
    icon?: string
    data?: any
  }>
  onAction?: ((action: string, data?: any) => void) | undefined
}> = ({ actions, onAction }) => {
  const getIcon = (iconName?: string) => {
    switch (iconName) {
      case 'zap': return <Zap className="w-4 h-4" />
      case 'package': return <Package className="w-4 h-4" />
      case 'refresh': return <RefreshCw className="w-4 h-4" />
      default: return null
    }
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h4 className="font-medium text-blue-800 mb-3">Quick Actions</h4>
      <div className="flex flex-wrap gap-2">
        {actions.map((action, index) => (
          <button
            key={index}
            onClick={() => onAction?.(action.action, action.data)}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            {getIcon(action.icon)}
            <span>{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

// Info Card Component
const InfoCard: React.FC<{
  info: {
    title: string
    message: string
    type: 'info' | 'success' | 'warning'
  }
  onAction?: ((action: string, data?: any) => void) | undefined
}> = ({ info }) => {
  const getIcon = () => {
    switch (info.type) {
      case 'success': return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'warning': return <AlertCircle className="w-5 h-5 text-yellow-500" />
      default: return <Info className="w-5 h-5 text-blue-500" />
    }
  }

  const getStyles = () => {
    switch (info.type) {
      case 'success': return 'bg-green-50 border-green-200 text-green-800'
      case 'warning': return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      default: return 'bg-blue-50 border-blue-200 text-blue-800'
    }
  }

  return (
    <div className={`border rounded-lg p-4 ${getStyles()}`}>
      <div className="flex items-start gap-3">
        {getIcon()}
        <div>
          <h4 className="font-medium mb-1">{info.title}</h4>
          <p className="text-sm">{info.message}</p>
        </div>
      </div>
    </div>
  )
}

// Loading Status Component
const LoadingStatus: React.FC<{
  status: {
    message: string
    progress?: number
    stage?: string
  }
}> = ({ status }) => {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
      <div className="flex items-center gap-3">
        <div className="animate-spin">
          <RefreshCw className="w-5 h-5 text-sparky-gold" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">{status.message}</p>
          {status.stage && (
            <p className="text-xs text-gray-600 mt-1">Current stage: {status.stage}</p>
          )}
          {status.progress !== undefined && (
            <div className="mt-2">
              <div className="bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-sparky-gold h-2 rounded-full transition-all duration-300"
                  style={{ width: `${status.progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default RichMessageContent