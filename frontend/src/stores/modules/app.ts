import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useWSStore } from './ws'

export const useAppStore = defineStore('app', () => {
  const wsStore = useWSStore()

  // UI 状态
  const showDialog = ref(false) // 对话框用户可见性（说话时自动隐藏）
  const showSiriWave = ref(false) // SiriWave 波形显示（仅在说话时）

  const buttonStates = ref({
    video: false
  })

  return {
    wsStore,
    showDialog,
    showSiriWave,
    buttonStates
  }
})
