import { defineStore } from 'pinia'
import { ref } from 'vue'
import { AudioPlayer } from '@/util/AudioPlayer'
import { useStageStore } from './stage'

export const useAudioStore = defineStore('audio', () => {
  const stageStore = useStageStore()
  const player = new AudioPlayer()

  const mouthOpen = ref(0) // 嘴巴张开程度 0-1
  const speakingCharacterId = ref<string | null>(null)

  /**
   * 播放音频并同步口型
   */
  const play = async (base64Data: string, characterId: string) => {
    speakingCharacterId.value = characterId
    try {
      await player.playBase64(base64Data, (volume) => {
        mouthOpen.value = volume
        if (characterId) {
          stageStore.updateCharacterTransform(characterId, { mouthOpen: volume })
        }
      })
    } finally {
      mouthOpen.value = 0
      speakingCharacterId.value = null
      if (characterId) {
        stageStore.updateCharacterTransform(characterId, { mouthOpen: 0 })
      }
    }
  }

  return {
    mouthOpen,
    speakingCharacterId,
    play
  }
})
