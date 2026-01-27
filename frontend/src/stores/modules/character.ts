import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface CharacterConfig {
  id: string
  name: string
  modelPath: string
  scale?: number
  position?: { x: number, y: number }
}

export const useCharacterStore = defineStore('character', () => {
  const characters = ref<Record<string, CharacterConfig>>({
    'maho': {
      id: 'maho',
      name: '比屋定真帆',
      modelPath: '/maho-l2d/maho.model3.json',
      scale: 0.4,
      position: { x: 0.5, y: 0.5 }
    },
    'may': {
      id: 'may',
      name: '椎名真由理',
      modelPath: '/MAY-l2d/MAY-live2d.model3.json',
      scale: 0.4,
      position: { x: 0.5, y: 0.5 }
    }
  })

  const activeCharacterIds = ref<string[]>(['maho', 'may'])

  const activeCharacters = computed(() => {
    return activeCharacterIds.value.map(id => characters.value[id]).filter(Boolean)
  })

  return {
    characters,
    activeCharacterIds,
    activeCharacters
  }
})
