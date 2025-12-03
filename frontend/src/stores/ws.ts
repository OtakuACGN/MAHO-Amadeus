import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import config from '../config.json'

export const useWsStore = defineStore('ws', () => {
  // 队列1：字符流（type: 'text'）
  const textQueue = ref<string[]>([])
  const audioQueue = ref<{ data: string, is_final: boolean }[]>([])
  const isWaiting = ref(true)
  const wsurl = ref(`ws://${config.ip}:8080/ws`)
  const wsStatus = ref('closed')
  let WS: WebSocket | null = null
  let reconnectTimer: number | null = null // 重连定时器
  const userName = ref(localStorage.getItem('username') || '未命名')
  const amadeusName = ref(config.amadeusName || '比屋定真帆')
  const currentName = ref(userName.value)

  function bindWebSocketEvents(ws: WebSocket) {
    ws.onopen = () => {
      console.log('WebSocket连接已建立', ws.url)
      wsStatus.value = 'connected'
      if (reconnectTimer) {
        clearInterval(reconnectTimer)
        reconnectTimer = null
      }
    }
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        switch (msg.type) {
          case 'text':
            textQueue.value.push(msg.data)
            break
          case 'audio':
            audioQueue.value.push({
              data: msg.data,
              is_final: msg.is_final
            })
            break
          case 'start':
            textQueue.value = []
            isWaiting.value = true
            currentName.value = amadeusName.value
            break
          case 'end':
            currentName.value = userName.value
            isWaiting.value = false
            break
          default:
            console.warn('未知的消息类型:', msg.type, msg)
            break
        }
      } catch (e) {
        console.error('WS消息解析失败', e)
      }
    }
    ws.onclose = () => {
      wsStatus.value = 'closed'
      reconnectWebSocket()
    }
  }

  function createWebSocket() {
    const ws = new WebSocket(wsurl.value)
    bindWebSocketEvents(ws)
    return ws
  }

  function reconnectWebSocket() {
    if (wsStatus.value === 'connected') return
    if (reconnectTimer) return
    reconnectTimer = window.setInterval(() => {
      if (!WS || WS.readyState === WebSocket.CLOSED) {
        console.log('尝试重新连接WebSocket...')
        WS = createWebSocket()
      }
    }, 3000)
  }

  // 初始化连接
  WS = createWebSocket()

  return {
    textQueue,
    audioQueue,
    isWaiting,
    WS,
    wsStatus,
    currentName
  }
})