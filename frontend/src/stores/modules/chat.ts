import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useWSStore } from './ws'
import { useAppStore } from './app'
import { useCharacterStore } from './character'

export const useChatStore = defineStore('chat', () => {
  const wsStore = useWSStore()
  const appStore = useAppStore()
  const characterStore = useCharacterStore()

  const textQueue = ref<string[]>([])
  const thinkText = ref('')
  const currentName = ref(appStore.userName)

  // 监听文本流
  wsStore.wsClient.on('thinkText', (msg: any) => {
    if (msg.character) {
      currentName.value = msg.character
    }
    thinkText.value += msg.data
  })

  wsStore.wsClient.on('text', (msg: any) => {
    if (msg.character) {
      currentName.value = msg.character
    }
    if (thinkText.value) {
      thinkText.value = ''
    }
    textQueue.value.push(msg.data)
  })

  // 监听对话生命周期
  wsStore.wsClient.on('start', (msg: any) => {
    textQueue.value = []
    thinkText.value = ''
    appStore.isWaiting = true
    currentName.value = msg?.character || (characterStore.activeCharacters[0]?.name) || 'Amadeus'
  })

  wsStore.wsClient.on('end', () => {
    currentName.value = appStore.userName
    appStore.isWaiting = false
  })

  return {
    textQueue,
    thinkText,
    currentName
  }
})
