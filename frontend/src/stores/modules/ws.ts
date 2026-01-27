import { defineStore } from 'pinia'
import { ref } from 'vue'
import { MahoWebSocket } from '../../api/ws'

export const useWSStore = defineStore('ws', () => {
  // WebSocket 客户端单例
  const wsClient = new MahoWebSocket()

  const wsStatus = ref('closed')

  // 基础连接监听
  wsClient.on('open', () => {
    wsStatus.value = 'connected'
  })

  wsClient.on('close', () => {
    wsStatus.value = 'closed'
  })

  function send(data: any) {
    wsClient.send(data)
  }

  return {
    wsClient,
    wsStatus,
    send
  }
})