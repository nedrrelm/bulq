import { useEffect, useRef, useState, useCallback } from 'react'

// WebSocket configuration constants
const WEBSOCKET_RECONNECT_INTERVAL_MS = 3000 // 3 seconds between reconnection attempts
const WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 5 // Maximum number of reconnection attempts
const WEBSOCKET_HEARTBEAT_INTERVAL_MS = 30000 // 30 seconds between heartbeat pings

interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onConnect?: () => void
  onDisconnect?: () => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useWebSocket(url: string | null, options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    reconnectInterval = WEBSOCKET_RECONNECT_INTERVAL_MS,
    maxReconnectAttempts = WEBSOCKET_MAX_RECONNECT_ATTEMPTS
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  const connect = useCallback(() => {
    if (!url) return

    try {
      // Close existing connection if any
      if (wsRef.current) {
        wsRef.current.close()
      }

      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setIsConnected(true)
        reconnectAttemptsRef.current = 0
        if (onConnect) onConnect()
      }

      ws.onmessage = (event) => {
        // Ignore pong responses (heartbeat)
        if (event.data === 'pong') {
          return
        }

        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          if (onMessage) onMessage(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onerror = (error) => {
        // Don't log errors if we're intentionally closing or reconnecting
        // These are expected during normal reconnection flow
        if (wsRef.current && wsRef.current.readyState === WebSocket.CLOSING) {
          return
        }
        console.error('WebSocket error:', error)
      }

      ws.onclose = (event) => {
        setIsConnected(false)
        wsRef.current = null
        if (onDisconnect) onDisconnect()

        // Don't reconnect on authentication errors (code 1008) or normal closure (code 1000)
        // Authentication errors mean the session is invalid and reconnecting won't help
        const shouldNotReconnect = event.code === 1008 || event.code === 1000

        // Attempt to reconnect for network/server errors
        if (!shouldNotReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else if (shouldNotReconnect) {
          // Log why we're not reconnecting
          console.log(`WebSocket closed (code ${event.code}): ${event.reason || 'No reason provided'}. Not reconnecting.`)
        }
      }
    } catch (err) {
      console.error('Failed to create WebSocket connection:', err)
    }
  }, [url, onConnect, onMessage, onDisconnect, reconnectInterval, maxReconnectAttempts])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    reconnectAttemptsRef.current = 0
    setIsConnected(false)
  }, [])

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof message === 'string' ? message : JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected')
    }
  }, [])

  useEffect(() => {
    if (url) {
      connect()
    }

    return () => {
      disconnect()
    }
  }, [url, connect, disconnect])

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!isConnected) return

    const interval = setInterval(() => {
      sendMessage('ping')
    }, WEBSOCKET_HEARTBEAT_INTERVAL_MS)

    return () => clearInterval(interval)
  }, [isConnected, sendMessage])

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect
  }
}
