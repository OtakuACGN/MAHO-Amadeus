import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { usePerformanceStore } from './performance'
import { useDialogStore } from './modules/dialog'
import { useAudioStore } from './modules/audio'
import { useStageStore } from './modules/stage'
import { useWSStore } from './modules/ws'

// 导演状态枚举
export enum DirectorState {
  InputStandby = 'InputStandby', // 等待用户输入
  Performance = 'Performance',   // 演出中
  Waiting = 'Waiting'            // 等待用户点击继续
}

export const useDirectorStore = defineStore('director', () => {
  // 依赖的 Store
  const performanceStore = usePerformanceStore()
  const dialogStore = useDialogStore()
  const audioStore = useAudioStore()
  const stageStore = useStageStore()
  const wsStore = useWSStore()

  // 状态
  const currentState = ref<DirectorState>(DirectorState.InputStandby)
  
  // 配置
  const textSpeed = ref(25) // 打字机速度：提高到每秒60字左右
  
  // 内部工具与变量
  let typeInterval: number | null = null
  let audioIndex = 0
  let isAudioFinished = ref(false)
  let isTextFinished = ref(false)
  let currentProcessingId: string | null = null

  // --- 状态流转控制 ---

  /**
   * 1. 切换到 [输入待机状态]
   */
  const enterInputStandby = () => {
    currentState.value = DirectorState.InputStandby
    dialogStore.canInput = true
    dialogStore.showCaret = true
    dialogStore.showDialog = true
    // 进入输入状态时，清理之前的内容
    dialogStore.dialogText = ''
    dialogStore.thinkText = ''
    // 将显示的名字改为用户
    dialogStore.currentName = '用户'
  }

  /**
   * 2. 切换到 [演出状态]
   */
  const enterPerformance = async () => {
    const act = performanceStore.headPerformance
    if (!act) return

    currentState.value = DirectorState.Performance
    currentProcessingId = act.uniqueId
    dialogStore.canInput = false
    dialogStore.showCaret = false
    dialogStore.showDialog = true
    
    // 清理文本显示区，准备输出 AI 内容
    dialogStore.dialogText = ''
    dialogStore.thinkText = ''
    
    // 同步角色信息
    dialogStore.currentName = act.characterId
    
    // 重置状态
    isAudioFinished.value = false
    isTextFinished.value = false
    audioIndex = 0
    
    // 开始打字机演出与音频异步播放
    startTypewriter(act)
    playNextAudio(act)
  }

  /**
   * 3. 切换到 [等待状态]
   */
  const enterWaiting = () => {
    currentState.value = DirectorState.Waiting
    dialogStore.canInput = false
    dialogStore.showCaret = true
  }

  // --- 演出逻辑实现 ---

  // 音频播放逻辑：使用循环代替递归，逻辑更清晰
  const playNextAudio = async (act: any) => {
    while (currentProcessingId === act.uniqueId) {
      if (audioIndex < act.audioChunks.length) {
        const chunk = act.audioChunks[audioIndex++]
        try {
          // 调用 AudioStore 统一播放接口，处理音频解码、播放及口型同步
          await audioStore.play(chunk.data, act.characterId)
        } catch (err) {
          console.warn('音频播放失败:', err)
        }
      } else if (!act.isSegmentComplete) {
        // 缓冲区空了但还没结束，等一等新数据
        await new Promise(resolve => setTimeout(resolve, 100))
      } else {
        // 数据已经全部传完且播完
        break
      }
    }

    // 播放结束后的状态标记
    if (currentProcessingId === act.uniqueId) {
      isAudioFinished.value = true
      checkFinish()
    }
  }

  // 打字机逻辑实现
  const startTypewriter = (act: any) => {
    if (typeInterval) clearInterval(typeInterval)
    
    let thinkIndex = 0
    let textIndex = 0
    let isThinkingPhase = true

    typeInterval = window.setInterval(() => {
      if (currentProcessingId !== act.uniqueId) {
        clearInterval(typeInterval!)
        return
      }

      // 阶段 1: 思考文本
      if (isThinkingPhase) {
        if (act.thinkText && thinkIndex < act.thinkText.length) {
          dialogStore.thinkText += act.thinkText[thinkIndex++]
        } else if (act.isThinkingComplete || (!act.thinkText && (act.text?.length || 0) > 0)) {
          // 如果思考结束，或者思考文本为空但正文已经来了，直接进正文
          dialogStore.thinkText = '' 
          isThinkingPhase = false    
          // 允许同一帧继续处理正文，减少等待
        }
      }
      
      // 阶段 2: 普通文本
      if (!isThinkingPhase) {
          if (act.text && textIndex < act.text.length) {
              dialogStore.dialogText += act.text[textIndex++]
          } else if (act.isSegmentComplete && textIndex >= (act.text?.length || 0)) {
              clearInterval(typeInterval!)
              isTextFinished.value = true
              checkFinish()
          }
      }
    }, 1000 / textSpeed.value)
  }

  const checkFinish = () => {
    if (isAudioFinished.value && isTextFinished.value) {
      enterWaiting()
    }
  }

  // --- 触发上面函数的地方 ---

  /**
   * 用户点击页面触发
   */
  const handleScreenClick = () => {
    if (currentState.value === DirectorState.Waiting) {
      performanceStore.popPerformance()
      if (performanceStore.queue.length > 0) {
        enterPerformance()
      } else {
        enterInputStandby()
      }
    }
  }

  // 监听队列：如果处于待机状态且来了新数据，自动开始
  watch(() => performanceStore.queue.length, (len) => {
    if (len > 0 && currentState.value === DirectorState.InputStandby) {
        enterPerformance()
    }
  })


  /**
   * 打断当前演出：通知后端停止生成，清空演出队列，回到输入待机状态
   * 注意：当前正在播放的音频会继续播放完，不会被强制中断
   */
  const interrupt = () => {
    // 1. 通知后端停止生成
    wsStore.send({ type: 'interrupt' })
    
    // 2. 停止打字机效果
    if (typeInterval) {
      clearInterval(typeInterval)
      typeInterval = null
    }
    
    // 3. 清空演出队列（后续待播放的内容被移除）
    performanceStore.clearQueue()
    currentProcessingId = null
    
    // 4. 重置状态标记
    isAudioFinished.value = false
    isTextFinished.value = false
    audioIndex = 0
    
    // 5. 切换到输入待机状态
    enterInputStandby()
  }

  return {
    currentState,
    textSpeed,
    handleScreenClick,
    enterInputStandby,
    interrupt
  }
})
