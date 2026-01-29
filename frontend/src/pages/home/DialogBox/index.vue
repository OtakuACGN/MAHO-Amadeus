<template>
  <div>
    <CenterRevealMask :visible="app.showDialog">
      <div class="dialog-container" :class="{ 'speaking-mode': dialog.isWaiting }">
        <DialogBackground />
        <meswinName :name="dialog.currentName" class="Meswinname" />
        <!-- DialogTextArea是主要的对话输入和显示组件，其他的一般都是装饰性的东西 -->
        <DialogTextArea 
          :thinkText="dialog.thinkText"
          :isInputMode="!dialog.isWaiting"
          :isPaused="dialog.isPaused"
          :textQueue="dialog.textQueue"
          @send="ws.send"
        />
      </div>
    </CenterRevealMask>
  </div>
</template>

<script setup lang="js">
import { onMounted, onUnmounted } from 'vue'
import { useGameStore } from '@/stores/game'
import CenterRevealMask from '@/component/CenterRevealMask.vue'
import DialogBackground from './DialogBackground.vue'
import meswinName from './meswinName.vue';
import DialogTextArea from './DialogTextArea/index.vue'

const gameStore = useGameStore()
const { app, dialog, ws } = gameStore

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
.dialog-container {
    transition: all 0.5s ease;
}

.speaking-mode {
    filter: drop-shadow(0 0 10px rgba(255, 153, 0, 0.4));
}

.Meswinname {
  position: absolute;
  bottom: 40px;
  /* 改为固定像素 */
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}
</style>
