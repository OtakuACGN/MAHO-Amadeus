import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useWSStore } from './ws'

export const useAppStore = defineStore('app', () => {
  const wsStore = useWSStore()

  // UI 状态
  const showSiriWave = ref(false) // SiriWave 波形显示（仅在说话时）

  const buttonStates = ref({
    video: false
  })

  return {
    wsStore,
    showSiriWave,
    buttonStates
  }
})
