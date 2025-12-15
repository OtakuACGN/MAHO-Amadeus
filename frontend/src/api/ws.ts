import config from '../config.json'

type MessageHandler = (data: any) => void
type EventHandler = () => void

// WebSocket通信封装类，支持事件/消息回调注册
export class MahoWebSocket {
  private ws: WebSocket | null = null
  private url: string
  private reconnectTimer: number | null = null
  private messageHandlers: Map<string, MessageHandler[]> = new Map()
  private eventHandlers: Map<string, EventHandler[]> = new Map()

  constructor() {
    this.url = `ws://${config.ip}:8080/ws`
    this.connect() // 实例化时自动连接
  }

  // 建立WebSocket连接
  private connect() {
    this.ws = new WebSocket(this.url)
    this.bindEvents()
  }

  // 绑定WebSocket原生事件，转发为自定义回调
  private bindEvents() {
    if (!this.ws) return

    this.ws.onopen = () => {
      console.log('WebSocket连接已建立', this.ws?.url)
      this.triggerEvent('open') // 触发open事件回调
      if (this.reconnectTimer) {
        clearInterval(this.reconnectTimer)
        this.reconnectTimer = null
      }
    }

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        this.triggerMessage(msg.type, msg) // 按type分发消息
      } catch (e) {
        console.error('WS消息解析失败', e)
      }
    }

    this.ws.onclose = () => {
      this.triggerEvent('close') // 触发close事件回调
      this.reconnect()
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      this.triggerEvent('error')
    }
  }

  // 自动重连机制
  private reconnect() {
    if (this.ws?.readyState === WebSocket.OPEN) return
    if (this.reconnectTimer) return

    this.reconnectTimer = window.setInterval(() => {
      if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
        console.log('尝试重新连接WebSocket...')
        this.connect()
      }
    }, 3000)
  }

  // 发送消息到后端
  public send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket未连接，无法发送消息')
    }
  }

  /**
   * 注册事件/消息回调
   * @param event 事件名（open/close/error/text/audio等）
   * @param callback 回调函数
   * 用法：ws.on('text', msg => { ... })
   */
  public on(event: string, callback: MessageHandler | EventHandler) {
    if (['open', 'close', 'error'].includes(event)) {
      if (!this.eventHandlers.has(event)) {
        this.eventHandlers.set(event, [])
      }
      this.eventHandlers.get(event)?.push(callback as EventHandler)
    } else {
      if (!this.messageHandlers.has(event)) {
        this.messageHandlers.set(event, [])
      }
      this.messageHandlers.get(event)?.push(callback as MessageHandler)
    }
  }

  private triggerEvent(event: string) {
    const handlers = this.eventHandlers.get(event)
    if (handlers) {
      handlers.forEach(handler => handler())
    }
  }

  private triggerMessage(type: string, data: any) {
    const handlers = this.messageHandlers.get(type)
    if (handlers) {
      handlers.forEach(handler => handler(data))
    } else {
      console.warn('未知的消息类型:', type, data)
    }
  }
}
