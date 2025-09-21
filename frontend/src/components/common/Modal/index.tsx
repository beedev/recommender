import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X } from 'lucide-react'
import { useAppSelector, useAppDispatch } from '@hooks/redux'
import { removeModal } from '@store/slices/uiSlice'
import Button from '../Button'

const Modal: React.FC = () => {
  const modals = useAppSelector(state => state.ui.modals)
  const dispatch = useAppDispatch()

  const handleClose = (modalId: string) => {
    dispatch(removeModal(modalId))
  }

  const handleBackdropClick = (e: React.MouseEvent, modalId: string) => {
    if (e.target === e.currentTarget) {
      handleClose(modalId)
    }
  }

  return (
    <AnimatePresence>
      {modals.map((modal, index) => (
        <motion.div
          key={modal.id}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ zIndex: 1000 + index }}
          onClick={(e) => handleBackdropClick(e, modal.id)}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm" />
          
          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="relative bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-hidden"
            role="dialog"
            aria-modal="true"
            aria-labelledby={`modal-title-${modal.id}`}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-neutral-200">
              <h3 
                id={`modal-title-${modal.id}`}
                className="text-lg font-semibold text-neutral-900"
              >
                {modal.title}
              </h3>
              <button
                type="button"
                className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-md transition-colors"
                onClick={() => handleClose(modal.id)}
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-4 overflow-y-auto">
              {typeof modal.content === 'string' ? (
                <p className="text-neutral-700">{modal.content}</p>
              ) : (
                modal.content
              )}
            </div>

            {/* Footer */}
            {(modal.onConfirm || modal.onCancel) && (
              <div className="flex items-center justify-end gap-3 p-4 border-t border-neutral-200">
                {modal.onCancel && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      modal.onCancel?.()
                      handleClose(modal.id)
                    }}
                  >
                    Cancel
                  </Button>
                )}
                {modal.onConfirm && (
                  <Button
                    variant="primary"
                    onClick={() => {
                      modal.onConfirm?.()
                      handleClose(modal.id)
                    }}
                  >
                    Confirm
                  </Button>
                )}
              </div>
            )}
          </motion.div>
        </motion.div>
      ))}
    </AnimatePresence>
  )
}

export default Modal