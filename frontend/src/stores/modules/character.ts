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

export const useCharacterStore = defineStore('character', () => {
  // 所有角色配置，键值对形式，包含激活状态
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

  return {
    characters,
    activeCharacters,
    updateCharacterTransform
  }
})
