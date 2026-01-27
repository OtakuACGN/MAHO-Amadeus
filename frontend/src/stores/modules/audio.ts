import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useWSStore } from './ws'

export const useAudioStore = defineStore('audio', () => {
  const wsStore = useWSStore()

  const audioQueue = ref<{ data: string, is_final: boolean }[]>([])
  const mouthOpen = ref(0) // 嘴巴张开程度 0-1
  const speakingCharacterId = ref<string | null>(null)

  // 监听音频流
  wsStore.wsClient.on('audio', (msg: any) => {
    if (msg.character) {
        speakingCharacterId.value = msg.character
    }
    audioQueue.value.push({
      data: msg.data,
      is_final: msg.is_final
    })
  })

  return {
    audioQueue,
    mouthOpen,
    speakingCharacterId
  }
})
