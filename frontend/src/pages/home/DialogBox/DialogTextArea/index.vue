<template>
  <div>
    <div v-if="thinkText.length > 1" id="think-div" class="dialog-textarea think-color">{{ thinkText }}</div>
    <div class="textarea-container">
      <textarea :readonly="!isInputMode" name="dialog-textarea" id="dialog-textarea" class="dialog-textarea"
        v-model="dialogText" @keydown.enter.prevent="sendTextToWS" ref="textareaRef"></textarea>
    </div>
    <CaretSprite :textarea="textareaRef" :text="dialogText" :visible="isInputMode || isPaused" :size="44" />
  </div>
</template>

<script setup lang="js">
import { ref, onMounted, nextTick, inject } from 'vue'
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
  isPaused: { // 新增属性
    type: Boolean,
    default: false
  },
  textQueue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['send'])

const dialogText = ref('')
const textareaRef = ref()
const isTyping = ref(false)

// 监听模式切换，如果是进入AI说话模式，清空文本
import { watch } from 'vue'
watch(() => props.isInputMode, (newVal) => {
  if (!newVal) {
    dialogText.value = ''
  }
})

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
      isTyping.value = false
      await new Promise(resolve => setTimeout(resolve, 100)); // 等待100ms再检查
      continue;
    }
    await nextTick(); // 等待下一帧，防止阻塞
    
    // 还原原本逻辑：流式追加显示。直接将队列中的内容合并显示
    // 因为后端本身就是流式输出，追加合并即能产生打字机效果
    const text = props.textQueue.join('');
    if (dialogText.value !== text) {
        dialogText.value = text;
        // 自动滚动到底部
        await nextTick();
        if (textareaRef.value) {
          textareaRef.value.scrollTop = textareaRef.value.scrollHeight;
        }
    }
    
    await new Promise(resolve => setTimeout(resolve, 50)); 
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

.textarea-container {
  position: relative;
  width: 100%;
  height: 100%;
}
</style>
