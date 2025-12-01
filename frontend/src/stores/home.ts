import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useHomeStore = defineStore('home', () => {
  const wsurl = ref('ws://localhost:8080/ws')
  let WS = new WebSocket(wsurl.value)
  console.log('WebSocket连接已建立：', wsurl.value)

  // 队列1：字符流（type: 'text'）
  const textQueue = ref<string[]>([])
  // 队列2：音频流（type: 'audio'）
  // 存储音频分片数据
  const audioQueue = ref<{data: string, is_final: boolean}[]>([])
  // 等待状态，用户输入后等待回复
  const isWaiting = ref(false)

  WS.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      switch (msg.type) {
        case 'text':
          textQueue.value.push(msg.data)
          break
        case 'audio':
          // 接收音频分片
          audioQueue.value.push({
            data: msg.data,
            is_final: msg.is_final
          })
          break
        case 'start':
          textQueue.value = []
          isWaiting.value = true
          break
        case 'end':
          isWaiting.value = false
          break
      }
    } catch (e) {
      // 非 JSON 或异常数据
      console.error('WS消息解析失败', e)
    }
  }

  WS.close = () => {
    console.log('WebSocket连接已关闭，尝试重新连接...')
    WS = new WebSocket(wsurl.value)
  }

  return {
    textQueue,
    audioQueue,
    isWaiting,
    WS
  }
})