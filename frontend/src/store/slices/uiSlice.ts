import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'

interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

interface Modal {
  id: string
  type: 'confirmation' | 'form' | 'custom'
  title: string
  content: string | React.ReactNode
  onConfirm?: () => void
  onCancel?: () => void
  props?: Record<string, unknown>
}

interface UIState {
  isLoading: boolean
  error: string | null
  theme: 'light' | 'dark' | 'system'
  language: string
  sidebarCollapsed: boolean
  toasts: Toast[]
  modals: Modal[]
  notifications: Array<{
    id: string
    type: 'info' | 'warning' | 'error' | 'success'
    title: string
    message: string
    read: boolean
    timestamp: string
  }>
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting'
}

const initialState: UIState = {
  isLoading: false,
  error: null,
  theme: (localStorage.getItem('theme') as 'light' | 'dark' | 'system') || 'system',
  language: localStorage.getItem('language') || 'en',
  sidebarCollapsed: JSON.parse(localStorage.getItem('sidebarCollapsed') || 'false'),
  toasts: [],
  modals: [],
  notifications: [],
  connectionStatus: 'connected',
}

// Async thunks
export const initializeApp = createAsyncThunk(
  'ui/initializeApp',
  async (_, { dispatch }) => {
    try {
      // Initialize theme
      const theme = localStorage.getItem('theme') || 'system'
      dispatch(setTheme(theme as 'light' | 'dark' | 'system'))

      // Initialize language
      const language = localStorage.getItem('language') || 'en'
      dispatch(setLanguage(language))

      return { theme, language }
    } catch (error) {
      throw new Error('Failed to initialize application')
    }
  }
)

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
    },
    clearError: state => {
      state.error = null
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'system'>) => {
      state.theme = action.payload
      localStorage.setItem('theme', action.payload)
      
      // Apply theme to document
      const root = document.documentElement
      if (action.payload === 'dark') {
        root.classList.add('dark')
      } else if (action.payload === 'light') {
        root.classList.remove('dark')
      } else {
        // System theme
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        if (prefersDark) {
          root.classList.add('dark')
        } else {
          root.classList.remove('dark')
        }
      }
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      state.language = action.payload
      localStorage.setItem('language', action.payload)
    },
    setSidebarCollapsed: (state, action: PayloadAction<boolean>) => {
      state.sidebarCollapsed = action.payload
      localStorage.setItem('sidebarCollapsed', JSON.stringify(action.payload))
    },
    addToast: (state, action: PayloadAction<Omit<Toast, 'id'>>) => {
      const toast: Toast = {
        ...action.payload,
        id: `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        duration: action.payload.duration || 5000,
      }
      state.toasts.push(toast)
    },
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter(toast => toast.id !== action.payload)
    },
    clearToasts: state => {
      state.toasts = []
    },
    addModal: (state, action: PayloadAction<Omit<Modal, 'id'>>) => {
      const modal: Modal = {
        ...action.payload,
        id: `modal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      }
      state.modals.push(modal)
    },
    removeModal: (state, action: PayloadAction<string>) => {
      state.modals = state.modals.filter(modal => modal.id !== action.payload)
    },
    clearModals: state => {
      state.modals = []
    },
    addNotification: (state, action: PayloadAction<Omit<UIState['notifications'][0], 'id' | 'read' | 'timestamp'>>) => {
      const notification = {
        ...action.payload,
        id: `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        read: false,
        timestamp: new Date().toISOString(),
      }
      state.notifications.unshift(notification)
      
      // Keep only last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50)
      }
    },
    markNotificationRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload)
      if (notification) {
        notification.read = true
      }
    },
    markAllNotificationsRead: state => {
      state.notifications.forEach(notification => {
        notification.read = true
      })
    },
    clearNotifications: state => {
      state.notifications = []
    },
    setConnectionStatus: (state, action: PayloadAction<'connected' | 'disconnected' | 'reconnecting'>) => {
      state.connectionStatus = action.payload
      
      // Only show critical connection lost notifications, not connection restored
      if (action.payload === 'disconnected') {
        const toast: Toast = {
          id: `connection-lost-${Date.now()}`,
          type: 'error',
          title: 'Connection Lost',
          message: 'Attempting to reconnect...',
          duration: 0, // Don't auto-dismiss
        }
        state.toasts = state.toasts.filter(t => !t.id.startsWith('connection-lost'))
        state.toasts.push(toast)
      } else if (action.payload === 'connected') {
        // Just clear the connection lost toast without showing success toast
        state.toasts = state.toasts.filter(t => !t.id.startsWith('connection-lost'))
      }
    },
  },
  extraReducers: builder => {
    builder
      .addCase(initializeApp.pending, state => {
        state.isLoading = true
      })
      .addCase(initializeApp.fulfilled, state => {
        state.isLoading = false
        state.error = null
      })
      .addCase(initializeApp.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || 'Failed to initialize application'
      })
  },
})

export const {
  setLoading,
  setError,
  clearError,
  setTheme,
  setLanguage,
  setSidebarCollapsed,
  addToast,
  removeToast,
  clearToasts,
  addModal,
  removeModal,
  clearModals,
  addNotification,
  markNotificationRead,
  markAllNotificationsRead,
  clearNotifications,
  setConnectionStatus,
} = uiSlice.actions

export const { actions } = uiSlice
export default uiSlice.reducer