import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useWSStore } from './modules/ws'

export interface AudioChunk {
  data: string // base64
  is_final: boolean
}

/**
 * 演出片段：存储一次完整对话的所有流式数据
 * 仅作为底层数据缓冲，不包含播放逻辑
 */
export interface PerformanceSegment {
  uniqueId: string
  characterId: string
  
  // 内容缓冲
  text: string
  thinkText: string
  audioChunks: AudioChunk[]
  
  // 状态标记
  isThinkingComplete: boolean
  isTextComplete: boolean
  isAudioComplete: boolean
  isSegmentComplete: boolean // 后端是否发送了总体的 'end' 信号
}

export const usePerformanceStore = defineStore('performance', () => {
    const wsStore = useWSStore()
    
    const queue = ref<PerformanceSegment[]>([])

    // 获取当前正在接收数据的 Segment (队尾)
    const activeReceiver = computed(() => {
        if (queue.value.length === 0) return null
        const last = queue.value[queue.value.length - 1]
        if (last.isSegmentComplete) return null
        return last
    })

    // --- 监听 WebSocket 消息，填充排队数据 ---
    
    wsStore.wsClient.on('start', (msg: any) => {
        const charId = msg.character || 'unknown'

        const newSegment: PerformanceSegment = {
            uniqueId: Date.now().toString() + Math.random().toString(36).substring(2, 7),
            characterId: charId,
            text: '',
            thinkText: '',
            audioChunks: [],
            isThinkingComplete: false,
            isTextComplete: false,
            isAudioComplete: false,
            isSegmentComplete: false
        }
        queue.value.push(newSegment)
    })

    wsStore.wsClient.on('text', (msg: any) => {
        if (activeReceiver.value && activeReceiver.value.characterId === msg.character) {
             activeReceiver.value.text += (msg.data || '')
             // 如果消息里包含结束标记可以设置 isTextComplete，目前默认为 true（因为是流式的）
        }
    })
    
    wsStore.wsClient.on('thinkText', (msg: any) => {
        if (activeReceiver.value && activeReceiver.value.characterId === msg.character) {
             activeReceiver.value.thinkText += (msg.data || '')
        }
    })

    wsStore.wsClient.on('audio', (msg: any) => {
         if (activeReceiver.value && (activeReceiver.value.characterId === msg.character || msg.character === undefined)) {
             activeReceiver.value.audioChunks.push({
                 data: msg.data,
                 is_final: msg.is_final
             })
             if (msg.is_final) {
                 activeReceiver.value.isAudioComplete = true
             }
         }
    })

    wsStore.wsClient.on('end', (msg: any) => {
        if (activeReceiver.value && (activeReceiver.value.characterId === msg.character || msg.character === undefined)) {
             activeReceiver.value.isSegmentComplete = true
             // 总体结束后，标记所有子状态完成
             activeReceiver.value.isThinkingComplete = true
             activeReceiver.value.isTextComplete = true
             activeReceiver.value.isAudioComplete = true
        }
    })
    
    const shiftSegment = () => {
        queue.value.shift()
    }
    
    const clearQueue = () => {
        queue.value = []
    }

    return {
        queue,
        activeReceiver,
        shiftSegment,
        clearQueue
    }
})
