import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useWSStore } from './ws'

export const useDialogStore = defineStore('dialog', () => {
  const wsStore = useWSStore()

  // 状态属性：只负责存储，决定渲染内容
  const canInput = ref(true)          // 决定是否可以输入
  const showCaret = ref(true)         // 决定是否显示光标
  const showDialog = ref(false)       // 决定对话框是否显示
  const currentName = ref('未命名')    // 当前显示的名称
  const thinkText = ref('')           // 深度思考文本
  const displayedText = ref('')       // 当前对话显示的文本

  // 用户输入提交回调
  const onInputSubmit = ref<(text: string) => void>((text: string) => {
    wsStore.send({
      type: 'chat',
      data: text,
      token: localStorage.getItem('token')
    })
  })


  return {
    canInput,
    showCaret,
    showDialog,
    currentName,
    thinkText,
    displayedText,
    onInputSubmit
  }
})
