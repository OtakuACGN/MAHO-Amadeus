import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAudioStore = defineStore('audio', () => {
  const mouthOpen = ref(0) // 嘴巴张开程度 0-1
  const speakingCharacterId = ref<string | null>(null)

  const setMouthOpen = (val: number) => {
    mouthOpen.value = val
  }

  const setSpeakingCharacter = (id: string | null) => {
    speakingCharacterId.value = id
  }

  return {
    mouthOpen,
    speakingCharacterId,
    setMouthOpen,
    setSpeakingCharacter
  }
})
