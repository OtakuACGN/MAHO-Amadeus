import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useWSStore } from './ws'
import { useCharacterStore } from './character'

export const useDialogStore = defineStore('dialog', () => {
  const wsStore = useWSStore()
  const characterStore = useCharacterStore()

  const isWaiting = ref(false)
  const userName = ref(localStorage.getItem('username') || '未命名')
  const textQueue = ref<string[]>([])
  const thinkText = ref('')
  const currentName = ref(userName.value)
  const isSpeaking = ref(false)
  const currentCharacterId = ref('')
  const isPaused = ref(false) // 是否暂停等待用户点击

  // 监听文本流
  wsStore.wsClient.on('thinkText', (msg: any) => {
    if (msg.character) {
      currentCharacterId.value = msg.character
      const char = characterStore.characters[msg.character]
      currentName.value = char?.name || msg.character
    }
    thinkText.value += msg.data
  })

  wsStore.wsClient.on('text', (msg: any) => {
    if (msg.character) {
      currentCharacterId.value = msg.character
      const char = characterStore.characters[msg.character]
      currentName.value = char?.name || msg.character
    }
    if (thinkText.value) {
      thinkText.value = ''
    }
    textQueue.value.push(msg.data)
  })

  // 监听对话生命周期
  wsStore.wsClient.on('start', (msg: any) => {
    isWaiting.value = true
    isSpeaking.value = true
    isPaused.value = false
    
    // 如果是第一次开始，清空上一轮的文本 (如果是连续对话通过 next 进来，不用清空，通过后端控制?)
    // 逻辑修正：start 意味着新角色的发言，应该清空文本框
    textQueue.value = []
    thinkText.value = ''
    
    if (msg?.character) {
      currentCharacterId.value = msg.character
      const char = characterStore.characters[msg.character]
      currentName.value = char?.name || msg.character
    } else {
      const firstActive = characterStore.activeCharacters[0]
      currentCharacterId.value = firstActive?.id || ''
      currentName.value = firstActive?.name || 'Amadeus'
    }
  })

  wsStore.wsClient.on('end', () => {
    // 角色发言结束，进入暂停状态
    isPaused.value = true
  })
  
  wsStore.wsClient.on('finish', () => {
    // 真正的全流程结束
    isSpeaking.value = false
    currentName.value = userName.value
    isWaiting.value = false
    isPaused.value = false
    currentCharacterId.value = ''
    // 可以不清空 textQueue，保留最后一句让用户看
  })

  return {
    isWaiting,
    userName,
    textQueue,
    thinkText,
    currentName,
    isSpeaking,
    currentCharacterId,
    isPaused
  }
})
