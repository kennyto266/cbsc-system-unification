class WebSocketService {
  private ws: WebSocket | null = null
  private store: any = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectTimeout = 3000

  connect(token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket('ws://localhost:3004/api/personal-strategies/ws/' + token)
        
        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          resolve()
        }

        this.ws.onclose = () => {
          console.log('WebSocket disconnected')
          this.reconnect(token)
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          reject(error)
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (error) {
            console.error('Error parsing WebSocket message:', error)
          }
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  private reconnect(token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`)
        this.connect(token)
      }, this.reconnectTimeout)
    }
  }

  private handleMessage(data: any) {
    console.log('WebSocket message:', data)
    // Handle different message types
    switch (data.type) {
      case 'ping':
        this.send({ type: 'pong' })
        break
      case 'performance_update':
        // Handle performance updates
        break
      case 'signal_update':
        // Handle trading signals
        break
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  subscribe(channel: string) {
    this.send({ type: 'subscribe', channel })
  }

  unsubscribe(channel: string) {
    this.send({ type: 'unsubscribe', channel })
  }

  setStore(store: any) {
    this.store = store
  }
}

const websocketService = new WebSocketService()
export default websocketService
