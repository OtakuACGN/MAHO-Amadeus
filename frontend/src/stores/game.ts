import { defineStore } from 'pinia'
import { useAppStore } from './modules/app'
import { useWSStore } from './modules/ws'
import { useCharacterStore } from './modules/character'
import { useChatStore } from './modules/chat'
import { useAudioStore } from './modules/audio'
import { useStageStore } from './modules/stage'

/**
 * 这是一个中转器 Store，它将各个领域的 Store 聚合在一起。
 * 方便开发者通过 gameStore.chat 或 gameStore.app 清晰地知道正在操作哪个模块。
 */
export const useGameStore = defineStore('game', () => {
  return {
    app: useAppStore(),
    ws: useWSStore(),
    char: useCharacterStore(),
    chat: useChatStore(),
    audio: useAudioStore(),
    stage: useStageStore()
  }
})
