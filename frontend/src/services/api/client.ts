import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { store } from '@store/index'
import { clearCredentials, refreshToken } from '@store/slices/authSlice'
import { addToast, setConnectionStatus } from '@store/slices/uiSlice'

// Base API configuration
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const state = store.getState()
    const token = state.auth.token
    
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // Update connection status on successful response
    store.dispatch(setConnectionStatus('connected'))
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    // Handle network errors
    if (!error.response) {
      store.dispatch(setConnectionStatus('disconnected'))
      store.dispatch(addToast({
        type: 'error',
        title: 'Network Error',
        message: 'Unable to connect to server. Please check your internet connection.',
      }))
      return Promise.reject(error)
    }

    // Handle 401 unauthorized - try to refresh token
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        await store.dispatch(refreshToken()).unwrap()
        
        // Retry original request with new token
        const state = store.getState()
        const newToken = state.auth.token
        if (newToken && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`
        }
        
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed, logout user
        store.dispatch(clearCredentials())
        store.dispatch(addToast({
          type: 'error',
          title: 'Session Expired',
          message: 'Please log in again.',
        }))
        
        // Redirect to login page
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // Handle other HTTP errors
    const errorMessage = getErrorMessage(error)
    store.dispatch(addToast({
      type: 'error',
      title: 'Request Failed',
      message: errorMessage,
    }))

    return Promise.reject(error)
  }
)

// Utility function to extract error messages
function getErrorMessage(error: AxiosError): string {
  if (error.response?.data) {
    const data = error.response.data as any
    if (typeof data.message === 'string') {
      return data.message
    }
    if (typeof data.error === 'string') {
      return data.error
    }
    if (typeof data.detail === 'string') {
      return data.detail
    }
  }
  
  if (error.message) {
    return error.message
  }
  
  return 'An unexpected error occurred'
}

// API wrapper functions for common operations
export const api = {
  // GET request
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.get(url, config).then(response => response.data)
  },

  // POST request
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.post(url, data, config).then(response => response.data)
  },

  // PUT request
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.put(url, data, config).then(response => response.data)
  },

  // PATCH request
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.patch(url, data, config).then(response => response.data)
  },

  // DELETE request
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    return apiClient.delete(url, config).then(response => response.data)
  },

  // Upload file
  upload: <T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> => {
    const formData = new FormData()
    formData.append('file', file)

    return apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100)
          onProgress(progress)
        }
      },
    }).then(response => response.data)
  },

  // Download file
  download: (url: string, filename?: string): Promise<void> => {
    return apiClient.get(url, {
      responseType: 'blob',
    }).then(response => {
      const blob = new Blob([response.data])
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename || 'download'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    })
  },
}

// Export the configured client for direct use if needed
export default apiClient