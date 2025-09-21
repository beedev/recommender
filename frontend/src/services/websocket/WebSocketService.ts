/**
 * WebSocket Service for Real-time Communication
 * Handles WebSocket connections for real-time updates from the enhanced orchestrator
 */

import { API_ENDPOINTS } from '@services/api/endpoints'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
  session_id?: string
}

export interface WebSocketConnectionStatus {
  status: 'connecting' | 'connected' | 'disconnected' | 'error'
  lastConnected?: Date
  reconnectAttempts: number
  error?: string
}

export type WebSocketEventHandler = (message: WebSocketMessage) => void

export class WebSocketService {
  private ws: WebSocket | null = null
  private eventHandlers = new Map<string, Set<WebSocketEventHandler>>()
  private connectionStatus: WebSocketConnectionStatus = {
    status: 'disconnected',
    reconnectAttempts: 0
  }
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null
  private readonly maxReconnectAttempts = 5
  private readonly reconnectDelay = 1000 // Start with 1 second
  private readonly heartbeatInterval = 30000 // 30 seconds
  private readonly maxReconnectDelay = 30000 // Max 30 seconds

  /**
   * Connect to WebSocket server
   */
  connect(sessionId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.disconnect() // Clean up any existing connection

        // Build WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const host = window.location.host
        let wsUrl = `${protocol}//${host}${API_ENDPOINTS.WEBSOCKET.CHAT}`
        
        if (sessionId) {
          wsUrl += `?session_id=${encodeURIComponent(sessionId)}`
        }

        this.connectionStatus.status = 'connecting'
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          this.connectionStatus = {
            status: 'connected',
            lastConnected: new Date(),
            reconnectAttempts: 0
          }
          
          this.startHeartbeat()
          this.notifyStatusChange()
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onclose = (event) => {
          this.stopHeartbeat()
          
          if (event.wasClean) {
            this.connectionStatus.status = 'disconnected'
          } else {
            this.connectionStatus.status = 'error'
            this.connectionStatus.error = `Connection closed unexpectedly (code: ${event.code})`
            this.scheduleReconnect()
          }
          
          this.notifyStatusChange()
        }

        this.ws.onerror = (error) => {
          this.connectionStatus.status = 'error'
          this.connectionStatus.error = 'WebSocket connection error'
          this.notifyStatusChange()
          reject(new Error('WebSocket connection failed'))
        }

        // Connection timeout
        setTimeout(() => {
          if (this.connectionStatus.status === 'connecting') {
            this.ws?.close()
            reject(new Error('WebSocket connection timeout'))
          }
        }, 10000) // 10 second timeout

      } catch (error) {
        this.connectionStatus.status = 'error'
        this.connectionStatus.error = 'Failed to create WebSocket connection'
        this.notifyStatusChange()
        reject(error)
      }
    })
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.clearReconnectTimer()
    this.stopHeartbeat()

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }

    this.connectionStatus.status = 'disconnected'
    this.notifyStatusChange()
  }

  /**
   * Send message through WebSocket
   */
  send(message: Omit<WebSocketMessage, 'timestamp'>): boolean {
    if (!this.isConnected()) {
      console.warn('Cannot send message: WebSocket not connected')
      return false
    }

    try {
      const fullMessage: WebSocketMessage = {
        ...message,
        timestamp: new Date().toISOString()
      }

      this.ws!.send(JSON.stringify(fullMessage))
      return true
    } catch (error) {
      console.error('Failed to send WebSocket message:', error)
      return false
    }
  }

  /**
   * Subscribe to WebSocket events
   */
  on(eventType: string, handler: WebSocketEventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set())
    }

    this.eventHandlers.get(eventType)!.add(handler)

    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(eventType)
      if (handlers) {
        handlers.delete(handler)
        if (handlers.size === 0) {
          this.eventHandlers.delete(eventType)
        }
      }
    }
  }

  /**
   * Subscribe to connection status changes
   */
  onStatusChange(handler: (status: WebSocketConnectionStatus) => void): () => void {
    return this.on('status_change', (message) => {
      handler(message.data as WebSocketConnectionStatus)
    })
  }

  /**
   * Get current connection status
   */
  getConnectionStatus(): WebSocketConnectionStatus {
    return { ...this.connectionStatus }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WebSocketMessage): void {
    // Notify specific event handlers
    const handlers = this.eventHandlers.get(message.type)
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error(`Error in WebSocket event handler for ${message.type}:`, error)
        }
      })
    }

    // Notify general message handlers
    const generalHandlers = this.eventHandlers.get('message')
    if (generalHandlers) {
      generalHandlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error('Error in general WebSocket message handler:', error)
        }
      })
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.connectionStatus.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('Max reconnection attempts reached')
      return
    }

    this.clearReconnectTimer()

    // Exponential backoff with jitter
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.connectionStatus.reconnectAttempts),
      this.maxReconnectDelay
    )
    const jitter = Math.random() * 1000 // Add up to 1 second of jitter

    this.reconnectTimer = setTimeout(() => {
      this.connectionStatus.reconnectAttempts++
      console.log(`Attempting to reconnect (attempt ${this.connectionStatus.reconnectAttempts}/${this.maxReconnectAttempts})`)
      
      this.connect().catch(error => {
        console.error('Reconnection failed:', error)
      })
    }, delay + jitter)
  }

  /**
   * Clear reconnection timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.send({
          type: 'ping',
          data: { timestamp: Date.now() }
        })
      }
    }, this.heartbeatInterval)
  }

  /**
   * Stop heartbeat timer
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * Notify status change to subscribers
   */
  private notifyStatusChange(): void {
    const statusHandlers = this.eventHandlers.get('status_change')
    if (statusHandlers) {
      const message: WebSocketMessage = {
        type: 'status_change',
        data: this.connectionStatus,
        timestamp: new Date().toISOString()
      }

      statusHandlers.forEach(handler => {
        try {
          handler(message)
        } catch (error) {
          console.error('Error in status change handler:', error)
        }
      })
    }
  }

  /**
   * Get service statistics
   */
  getStats(): Record<string, any> {
    return {
      connected: this.isConnected(),
      status: this.connectionStatus.status,
      reconnectAttempts: this.connectionStatus.reconnectAttempts,
      lastConnected: this.connectionStatus.lastConnected,
      eventHandlerCount: Array.from(this.eventHandlers.values())
        .reduce((total, handlers) => total + handlers.size, 0),
      eventTypes: Array.from(this.eventHandlers.keys())
    }
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService()