<template>
  <div>
    <div v-if="dialogStore.thinkText.length > 1" class="dialog-textarea think-color">
      {{ dialogStore.thinkText }}
    </div>
    <div class="textarea-container">
      <textarea 
        :readonly="!dialogStore.canInput" 
        class="dialog-textarea"
        v-model="dialogStore.userInput" 
        @keydown.enter.prevent="handleEnter" 
        ref="textareaRef"
      ></textarea>
    </div>
    <CaretSprite 
      :textarea="textareaRef" 
      :text="dialogStore.userInput" 
      :visible="dialogStore.showCaret" 
      :size="44"
    />
  </div>
</template>

<script setup lang="js">
import { ref, watch, nextTick } from 'vue'
import { useDialogStore } from '@/stores/modules/dialog'
import CaretSprite from './CaretSprite.vue'

const dialogStore = useDialogStore()
const textareaRef = ref()

// 监听 AI 文本展示
watch(() => dialogStore.displayedText, async (val) => {
  if (!dialogStore.canInput) {
    dialogStore.userInput = val
    await nextTick()
    if (textareaRef.value) {
      textareaRef.value.scrollTop = textareaRef.value.scrollHeight
    }
  }
})

const handleEnter = (e) => {
  if (!e.shiftKey && dialogStore.canInput) {
    const text = dialogStore.userInput.trim()
    if (text) {
      dialogStore.onInputSubmit(text)
    }
  }
}
</script>

<style scoped>
.dialog-textarea {
  background: rgba(0, 0, 0, 0.0);
  color: #e6e6e6;
  font-family: 'Microsoft YaHei', 'SimHei', '黑体', 'STHeiti', sans-serif;
  font-size: 2.2rem;
  text-shadow: 2px 2px 6px #000, 0 0 1px #fff;
  padding: 0 14vw;
  border: none;
  border-radius: 0.2em;
  letter-spacing: 0.05em;
  line-height: 1.6;
  box-sizing: border-box;
  border-bottom: 2px solid #e6a23c;
  position: absolute;
  bottom: 0;
  left: 0;
  resize: none;

  width: 100%;
  height: 246px;
  /* 改为固定像素 */
  overflow-y: auto;
  /* 保持可滚动 */
  scrollbar-width: none;
  /* Firefox 隐藏滚动条 */
}

.dialog-textarea::-webkit-scrollbar {
  width: 0px;
  /* Chrome/Safari 隐藏滚动条 */
  background: transparent;
}

.think-color {
  color: #888888;
  font-style: italic;
}

.textarea-container {
  position: relative;
  width: 100%;
  height: 100%;
}
</style>
