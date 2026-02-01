import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface CharacterConfig {
  id: string
  name: string
  modelPath: string
  scale?: number
  position?: { x: number, y: number }
  isActive: boolean
}

export interface BackgroundConfig {
  path: string
  alpha?: number
  scaleMode?: 'cover' | 'contain' | 'stretch'
}

export const useStageStore = defineStore('stage', () => {
  // 角色配置
  const characters = ref<Record<string, CharacterConfig>>({
    'maho': {
      id: 'maho',
      name: '比屋定真帆',
      modelPath: '/maho-l2d/maho.model3.json',
      scale: 0.4,
      position: { x: 0.5, y: 0.5 },
      isActive: true
    },
    'may': {
      id: 'may',
      name: '椎名真由理',
      modelPath: '/MAY-l2d/MAY-live2d.model3.json',
      scale: 0.4,
      position: { x: 0.5, y: 0.5 },
      isActive: true
    }
  })

  const activeCharacters = computed(() => {
    return Object.values(characters.value).filter(c => c.isActive)
  })

  const updateCharacterTransform = (id: string, transform: Partial<CharacterConfig>) => {
    if (characters.value[id]) {
      characters.value[id] = { ...characters.value[id], ...transform }
    }
  }

  // 舞台背景配置
  const background = ref<BackgroundConfig>({
    path: '/bg.png',
    alpha: 1,
    scaleMode: 'cover'
  })

  const setBackground = (path: string) => {
    background.value.path = path
  }

  return {
    characters,
    activeCharacters,
    updateCharacterTransform,
    background,
    setBackground
  }
})