<template>
  <div>
    <CenterRevealMask :visible="app.showDialog">
      <DialogBackground />
      <meswinName :name="chat.currentName" class="Meswinname" />
      <DialogTextArea 
        :thinkText="chat.thinkText"
        :isInputMode="!app.isWaiting"
        :textQueue="chat.textQueue"
        @send="app.send"
      />
    </CenterRevealMask>
  </div>
</template>

<script setup lang="js">
import { onMounted, onUnmounted } from 'vue'
import { useGameStore } from '@/stores/game'
import CenterRevealMask from '@/component/CenterRevealMask.vue'
import DialogBackground from '@/component/DialogBox/DialogBackground.vue'
import meswinName from '@/component/DialogBox/meswinName.vue';
import DialogTextArea from '@/component/DialogBox/DialogTextArea.vue'

const gameStore = useGameStore()
const { app, chat } = gameStore

// 是否显示/隐藏对话框
const handleKeyDown = (e) => {
  if (e.key.toLowerCase() === 'h' && e.shiftKey) {
    app.showDialog = !app.showDialog
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
  setTimeout(() => {
    app.showDialog = true
  }, 1000)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
})
</script>

<style>
.Meswinname {
  position: absolute;
  bottom: 40px;
  /* 改为固定像素 */
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}
</style>
