<template>
  <div>
    <CenterRevealMask :visible="dialog.showDialog">
      <div class="dialog-container">
        <DialogBackground />
        <meswinName :name="dialog.currentName" class="Meswinname" />
        <DialogTextArea />
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
const { dialog } = gameStore

// 是否显示/隐藏对话框
const handleKeyDown = (e) => {
  if (e.key.toLowerCase() === 'h' && e.shiftKey) {
    dialog.showDialog = !dialog.showDialog
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
  setTimeout(() => {
    dialog.showDialog = true
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
