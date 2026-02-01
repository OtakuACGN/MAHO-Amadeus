import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useWSStore } from './ws'
import { useStageStore } from './stage'

export interface AudioChunk {
  data: string // base64
  is_final: boolean
}

export interface PerformanceSegment {
  uniqueId: string
  characterId: string
  characterName: string
  
  // 内容缓冲
  text: string
  thinkText: string
  audioChunks: AudioChunk[]
  
  // 状态标记
  isSegmentComplete: boolean // 后端是否发送了 'end' 信号
}

export const usePerformanceStore = defineStore('performance', () => {
    const wsStore = useWSStore()
    const stageStore = useStageStore() 
    
    const queue = ref<PerformanceSegment[]>([])
    const isAutoPlay = ref(true) // 前端播放完毕后是否自动请求下一句(如果后端需要信号)
    // 注意：现在的后端不需要 Next 信号了，所以这个 flag 主要用于“自动开始播放下一段”

    // 获取当前正在接收数据的 Segment (通常是队尾那个，且尚未完成)
    const activeReceiver = computed(() => {
        if (queue.value.length === 0) return null
        const last = queue.value[queue.value.length - 1]
        // 如果最后一个已经标记完成了，说明新的还没 start，返回 null
        if (last.isSegmentComplete) return null
        return last
    })

    // 获取当前应该播放的 Segment (队头)
    const currentPlayingSegment = computed(() => {
        if (queue.value.length === 0) return null
        return queue.value[0]
    })

    // --- 监听 WebSocket 消息 ---

    wsStore.wsClient.on('start', (msg: any) => {
        const charId = msg.character || 'unknown'
        // 尝试从舞台配置获取角色名
        const charConfig = stageStore.characters[charId]
        const charName = charConfig ? charConfig.name : charId

        const newSegment: PerformanceSegment = {
            uniqueId: Date.now().toString() + Math.random().toString(36).substr(2, 5),
            characterId: charId,
            characterName: charName,
            text: '',
            thinkText: '',
            audioChunks: [],
            isSegmentComplete: false
        }
        queue.value.push(newSegment)
    })

    wsStore.wsClient.on('text', (msg: any) => {
        if (activeReceiver.value && activeReceiver.value.characterId === msg.character) {
             activeReceiver.value.text += msg.data
        }
    })
    
    wsStore.wsClient.on('thinkText', (msg: any) => {
        if (activeReceiver.value && activeReceiver.value.characterId === msg.character) {
             activeReceiver.value.thinkText += msg.data
        }
    })

    wsStore.wsClient.on('audio', (msg: any) => {
         if (activeReceiver.value && activeReceiver.value.characterId === msg.character) {
             activeReceiver.value.audioChunks.push({
                 data: msg.data,
                 is_final: msg.is_final
             })
         }
    })

    wsStore.wsClient.on('end', (msg: any) => {
        if (activeReceiver.value && activeReceiver.value.characterId === msg.character) {
             activeReceiver.value.isSegmentComplete = true
        }
    })
    
    // 监听中断或其他控制信号
    wsStore.wsClient.on('finish', () => {
        // 整个脚本结束
    })

    // --- Actions ---
    
    // 播放完毕，移除队头
    const shiftSegment = () => {
        queue.value.shift()
    }
    
    const clearQueue = () => {
        queue.value = []
    }

    return {
        queue,
        isAutoPlay,
        currentPlayingSegment,
        activeReceiver,
        shiftSegment,
        clearQueue
    }
})
