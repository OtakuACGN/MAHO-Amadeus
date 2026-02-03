import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { usePerformanceStore } from './performance'
import { useDialogStore } from './modules/dialog'
import { useAudioStore } from './modules/audio'
import { useStageStore } from './modules/stage'
import { AudioPlayer } from '@/util/AudioPlayer'

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

  // 状态
  const currentState = ref<DirectorState>(DirectorState.InputStandby)
  
  // 配置
  const textSpeed = ref(25) // 打字机速度：提高到每秒60字左右
  
  // 内部工具与变量
  const audioPlayer = new AudioPlayer()
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
    // 进入输入状态时，清理之前的状态和输入框
    dialogStore.userInput = ''
    dialogStore.displayedText = ''
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
    dialogStore.displayedText = ''
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

  // 音频播放逻辑：递归播放数组中的音频片
  const playNextAudio = async (act: any) => {
    if (currentProcessingId !== act.uniqueId) return

    if (audioIndex < act.audioChunks.length) {
      const chunk = act.audioChunks[audioIndex]
      audioIndex++
      
      // 设置正在说话的角色
      audioStore.setSpeakingCharacter(act.characterId)
      
      try {
        await audioPlayer.playBase64(chunk.data, (volume) => {
          // 更新全局口型与角色配置
          audioStore.setMouthOpen(volume)
          if (act.characterId) {
             stageStore.updateCharacterTransform(act.characterId, { mouthOpen: volume })
          }
        })
      } catch (err) {
        console.warn('音频解码失败，跳过该片段:', err)
      }

      playNextAudio(act)
    } else {
      if (!act.isSegmentComplete) {
        setTimeout(() => playNextAudio(act), 100)
        return
      }
      
      audioStore.setSpeakingCharacter(null)
      audioStore.setMouthOpen(0)
      stageStore.updateCharacterTransform(act.characterId, { mouthOpen: 0 })
      isAudioFinished.value = true
      checkFinish()
    }
  }

  // 打字机逻辑实现
  const startTypewriter = (act: any) => {
    if (typeInterval) clearInterval(typeInterval)
    dialogStore.thinkText = ''
    dialogStore.displayedText = ''
    
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
          dialogStore.thinkText += act.thinkText[thinkIndex]
          thinkIndex++
        } else if (act.isThinkingComplete || (!act.thinkText && act.text.length > 0)) {
          // 如果思考结束，或者思考文本为空但正文已经来了，直接进正文
          dialogStore.thinkText = '' 
          isThinkingPhase = false    
        }
      }
      
      // 阶段 2: 普通文本
      if (!isThinkingPhase) {
          if (act.text && textIndex < act.text.length) {
              dialogStore.displayedText += act.text[textIndex]
              textIndex++
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


  return {
    currentState,
    textSpeed,
    handleScreenClick,
    enterInputStandby
  }
})
