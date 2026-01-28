import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface BackgroundConfig {
  path: string
  alpha?: number
  scaleMode?: 'cover' | 'contain' | 'stretch'
}

export const useStageStore = defineStore('stage', () => {
  const background = ref<BackgroundConfig>({
    path: '/bg.png',
    alpha: 1,
    scaleMode: 'cover'
  })

  const setBackground = (path: string) => {
    background.value.path = path
  }

  return {
    background,
    setBackground
  }
})
