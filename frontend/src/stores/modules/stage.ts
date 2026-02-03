import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface CharacterConfig {
  id: string
  name: string
  modelPath: string
  scale?: number
  position?: { x: number, y: number }
  mouthOpen: number // 嘴巴张开幅度 (0-1)
}

export interface BackgroundConfig {
  path: string
  alpha?: number
  scaleMode?: 'cover' | 'contain' | 'stretch'
}

export const useStageStore = defineStore('stage', () => {
  // 角色配置
  const characters = ref<CharacterConfig[]>([
    {
      id: 'maho',
      name: '比屋定真帆',
      modelPath: '/maho-l2d/maho.model3.json',
      scale: 0.32,
      position: { x: 0.3, y: 0.65 },
      mouthOpen: 0
    },
    {
      id: 'mayuri',
      name: '椎名真由理',
      modelPath: '/MAY-l2d/MAY-live2d.model3.json',
      scale: 0.4,
      position: { x: 0.7, y: 0.6 },
      mouthOpen: 0
    }
  ])

  // 更新指定角色的变换配置，通过id
  const updateCharacterTransform = (id: string, transform: Partial<CharacterConfig>) => {
    const index = characters.value.findIndex(c => c.id === id)
    if (index !== -1) {
      characters.value[index] = { ...characters.value[index], ...transform }
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
    updateCharacterTransform,
    background,
    setBackground
  }
})