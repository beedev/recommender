import React, { useState } from 'react'
import { RotateCcw, AlertTriangle, CheckCircle } from 'lucide-react'

interface ConversationResetProps {
  onReset: () => void
  onCancel?: () => void
  messageCount?: number
  hasPackages?: boolean
  className?: string
}

export const ConversationReset: React.FC<ConversationResetProps> = ({
  onReset,
  onCancel,
  messageCount = 0,
  hasPackages = false,
  className = ''
}) => {
  const [isConfirming, setIsConfirming] = useState(false)
  const [isResetting, setIsResetting] = useState(false)

  const handleResetClick = () => {
    if (messageCount === 0) {
      // No messages to reset, just reset immediately
      handleConfirmReset()
    } else {
      setIsConfirming(true)
    }
  }

  const handleConfirmReset = async () => {
    setIsResetting(true)
    try {
      await onReset()
      setIsConfirming(false)
    } catch (error) {
      console.error('Failed to reset conversation:', error)
    } finally {
      setIsResetting(false)
    }
  }

  const handleCancel = () => {
    setIsConfirming(false)
    onCancel?.()
  }

  if (isConfirming) {
    return (
      <div className={`conversation-reset-confirm ${className}`}>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-medium text-gray-900 mb-2">Reset Conversation?</h3>
              <p className="text-sm text-gray-600 mb-3">
                This will clear all {messageCount} messages and start a fresh conversation with Sparky.
                {hasPackages && ' Any package recommendations will also be cleared.'}
              </p>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={handleConfirmReset}
                  disabled={isResetting}
                  className="flex items-center gap-2 px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isResetting ? (
                    <>
                      <div className="animate-spin w-3 h-3 border border-white border-t-transparent rounded-full" />
                      <span>Resetting...</span>
                    </>
                  ) : (
                    <>
                      <RotateCcw className="w-3 h-3" />
                      <span>Yes, Reset</span>
                    </>
                  )}
                </button>
                
                <button
                  onClick={handleCancel}
                  disabled={isResetting}
                  className="px-3 py-2 text-sm border border-gray-300 text-gray-700 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <button
      onClick={handleResetClick}
      className={`conversation-reset-button ${className}`}
      title="Reset conversation"
    >
      <RotateCcw className="w-4 h-4" />
    </button>
  )
}

// Success notification component
export const ResetSuccessNotification: React.FC<{
  onDismiss: () => void
  autoHide?: boolean
  hideDelay?: number
}> = ({ onDismiss, autoHide = true, hideDelay = 3000 }) => {
  React.useEffect(() => {
    if (autoHide) {
      const timer = setTimeout(onDismiss, hideDelay)
      return () => clearTimeout(timer)
    }
    return undefined
  }, [autoHide, hideDelay, onDismiss])

  return (
    <div className="fixed top-4 right-4 z-50 bg-green-50 border border-green-200 rounded-lg p-4 shadow-lg">
      <div className="flex items-center gap-3">
        <CheckCircle className="w-5 h-5 text-green-500" />
        <div>
          <p className="text-sm font-medium text-green-800">Conversation Reset</p>
          <p className="text-xs text-green-600">Starting fresh with Sparky</p>
        </div>
        <button
          onClick={onDismiss}
          className="text-green-400 hover:text-green-600 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  )
}

export default ConversationReset