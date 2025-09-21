import React, { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react'
import clsx from 'clsx'
import { useAppSelector, useAppDispatch } from '@hooks/redux'
import { removeToast } from '@store/slices/uiSlice'

const iconMap = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const colorMap = {
  success: {
    bg: 'bg-success-50',
    border: 'border-success-200',
    icon: 'text-success-500',
    title: 'text-success-800',
    message: 'text-success-700',
  },
  error: {
    bg: 'bg-error-50',
    border: 'border-error-200',
    icon: 'text-error-500',
    title: 'text-error-800',
    message: 'text-error-700',
  },
  warning: {
    bg: 'bg-warning-50',
    border: 'border-warning-200',
    icon: 'text-warning-500',
    title: 'text-warning-800',
    message: 'text-warning-700',
  },
  info: {
    bg: 'bg-info-50',
    border: 'border-info-200',
    icon: 'text-info-500',
    title: 'text-info-800',
    message: 'text-info-700',
  },
}

const Toast: React.FC = () => {
  const toasts = useAppSelector(state => state.ui.toasts)
  const dispatch = useAppDispatch()

  useEffect(() => {
    const timers = toasts.map(toast => {
      if (toast.duration && toast.duration > 0) {
        return setTimeout(() => {
          dispatch(removeToast(toast.id))
        }, toast.duration)
      }
      return null
    })

    return () => {
      timers.forEach(timer => {
        if (timer) clearTimeout(timer)
      })
    }
  }, [toasts, dispatch])

  return (
    <div
      className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md w-full pointer-events-none"
      aria-live="polite"
      aria-label="Notifications"
    >
      <AnimatePresence>
        {toasts.map(toast => {
          const Icon = iconMap[toast.type]
          const colors = colorMap[toast.type]

          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: -50, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -50, scale: 0.95 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
              className={clsx(
                'rounded-lg border p-4 shadow-lg backdrop-blur-sm pointer-events-auto',
                colors.bg,
                colors.border
              )}
              role="alert"
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0">
                  <Icon className={clsx('w-5 h-5', colors.icon)} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <h4 className={clsx('text-sm font-medium', colors.title)}>
                    {toast.title}
                  </h4>
                  {toast.message && (
                    <p className={clsx('mt-1 text-sm', colors.message)}>
                      {toast.message}
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  className="flex-shrink-0 p-1 rounded-md hover:bg-black hover:bg-opacity-10 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent focus:ring-neutral-400 transition-colors"
                  onClick={() => dispatch(removeToast(toast.id))}
                  aria-label="Dismiss notification"
                >
                  <X className="w-4 h-4 text-neutral-400" />
                </button>
              </div>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}

export default Toast