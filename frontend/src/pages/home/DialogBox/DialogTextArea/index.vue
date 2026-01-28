<template>
  <div>
    <div v-if="thinkText.length > 1" id="think-div" class="dialog-textarea think-color">{{ thinkText }}</div>
    <textarea :readonly="!isInputMode" name="dialog-textarea" id="dialog-textarea" class="dialog-textarea"
      v-model="dialogText" @keydown.enter.prevent="sendTextToWS" ref="textareaRef"></textarea>
    <CaretSprite :textarea="textareaRef" :text="dialogText" :visible="isInputMode" :size="44" />
  </div>
</template>

<script setup lang="js">
import { ref, onMounted, nextTick } from 'vue'
import CaretSprite from './CaretSprite.vue'

const props = defineProps({
  thinkText: {
    type: String,
    default: ''
  },
  isInputMode: {
    type: Boolean,
    default: true
  },
  textQueue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['send'])

const dialogText = ref('')
const textareaRef = ref()

function sendTextToWS(e) {
  if (!e.shiftKey && props.isInputMode) {
    const message = dialogText.value.trim();
    if (message) {
      emit('send', { type: 'chat', data: message, token: localStorage.getItem('token') });
      dialogText.value = ''; // 发送后清空输入框
    }
  }
}

async function processTextQueue() {
  while (true) {
    if (props.isInputMode) {
      await new Promise(resolve => setTimeout(resolve, 100)); // 等待100ms再检查
      continue;
    }
    await nextTick(); // 等待下一帧，防止阻塞
    // 取出所有字符并筛选
    const filtered = props.textQueue.filter(ch => ch !== '\n' && ch.trim() !== '');
    dialogText.value = filtered.join('');
    await new Promise(resolve => setTimeout(resolve, 100)); // 100ms轮询
  }
}

onMounted(() => {
  processTextQueue();
})
</script>

<style scoped>
.dialog-textarea {
  background: rgba(0, 0, 0, 0.0);
  color: #e6e6e6;
  font-family: 'Microsoft YaHei', 'SimHei', '黑体', 'STHeiti', sans-serif;
  font-size: 2.2rem;
  /* 改为固定像素 */
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
</style>
