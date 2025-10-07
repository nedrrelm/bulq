import { useEffect, useRef, useState, useCallback } from 'react'

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
    reconnectInterval = 3000,
    maxReconnectAttempts = 5
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
        console.log(`WebSocket connected: ${url}`)
        setIsConnected(true)
        reconnectAttemptsRef.current = 0
        if (onConnect) onConnect()
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          setLastMessage(message)
          if (onMessage) onMessage(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      ws.onclose = (event) => {
        console.log(`WebSocket disconnected: ${url}`, {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        })
        setIsConnected(false)
        wsRef.current = null
        if (onDisconnect) onDisconnect()

        // Attempt to reconnect
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`)
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
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
    }, 30000) // Send ping every 30 seconds

    return () => clearInterval(interval)
  }, [isConnected, sendMessage])

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect
  }
}
