<template>
  <div>
    <CenterRevealMask :visible="showMask">
      <img src="/meswin.png" alt="图片丢失" class="bg">
      <meswinName :name="currentName" class="Meswinname" />
      <textarea :readonly="isWaiting" name="dialog-textarea" id="dialog-textarea" class="dialog-textarea"
        v-model="dialogText" @keyup="sendTextToWS" ref="textareaRef"></textarea>
      <SpritePlayer v-if="!isWaiting" src="/ring.png" :rows="12" :columns="5" :fps="45" :width="spriteSize"
        :height="spriteSize" :totalFrames="60" :loop="0"
        :style="{ position: 'fixed', left: caretX + 'px', top: caretY + 'px', pointerEvents: 'none', zIndex: 9999 }" />
    </CenterRevealMask>
  </div>
</template>

<script setup lang="js">
import meswinName from '@/component/meswinName.vue';
import { useWsStore } from '@/stores/ws';
import { ref, onMounted, nextTick } from 'vue'
import { storeToRefs } from 'pinia'
import CenterRevealMask from '../component/CenterRevealMask.vue'
import SpritePlayer from '../component/SpritePlayer.vue'
// @ts-ignore
import getCaretCoordinates from 'textarea-caret';

const wsStore = useWsStore()
const { textQueue, isWaiting, currentName } = storeToRefs(wsStore)
const WS = wsStore.WS
const showMask = ref(false)

const dialogText = ref('');
const caretX = ref(0)
const caretY = ref(0)
const textareaRef = ref()
const spriteSize = ref(window.innerWidth * 0.025)

function updateCaret() {
  const textarea = textareaRef.value;
  if (!textarea) return
  const pos = textarea.value.length; // 末尾位置
  const coords = getCaretCoordinates(textarea, pos);
  caretX.value = coords.left + window.innerWidth * 0.018
  caretY.value = coords.top + window.innerWidth * 0.008
}

function sendTextToWS(e) {
  if (e.key === 'Enter' && !e.shiftKey && !isWaiting.value) {
    e.preventDefault(); // 阻止默认的换行行为
    const message = dialogText.value.trim();
    if (message) {
      WS.send(JSON.stringify({ type: 'chat', data: message, token: localStorage.getItem('token') }));
      dialogText.value = ''; // 发送后清空输入框
    }
  }
}

async function processTextQueue() {
  while (true) {
    updateCaret(); // 更新光标位置
    if (!isWaiting.value) {
      await new Promise(resolve => setTimeout(resolve, 100)); // 等待100ms再检查
      continue;
    }
    await nextTick(); // 等待下一帧，防止阻塞
    // 取出所有字符并筛选
    const filtered = textQueue.value.filter(ch => ch !== '\n' && ch.trim() !== '');
    dialogText.value = filtered.join('');
    await new Promise(resolve => setTimeout(resolve, 100)); // 100ms轮询
  }
}

// 打开和关闭遮罩，打开的时候等800ms是因为精灵图加载会卡顿，影响遮罩动画
function openMask() {
  showMask.value = true
  setTimeout(() => {
    isWaiting.value = false
  }, 800)
}

function closeMask() {
  showMask.value = false
  isWaiting.value = true
}

window.addEventListener('keydown', (e) => {
  if (e.key.toLowerCase() === 'h') {
    if (showMask.value) {
      closeMask();
    } else {
      openMask();
    }
  }
});

onMounted(() => {
  processTextQueue();
  setTimeout(() => {
    openMask()
    updateCaret()
  }, 1000)
})
</script>

<style>
.Meswinname {
  position: absolute;
  bottom: 2vw;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

.dialog-textarea {
  background: rgba(0, 0, 0, 0.0);
  color: #e6e6e6;
  font-family: 'Microsoft YaHei', 'SimHei', '黑体', 'STHeiti', sans-serif;
  font-size: 2.1vw;
  text-shadow: 2px 2px 6px #000, 0 0 1px #fff;
  padding: 0em 6em;
  border: none;
  border-radius: 0.2em;
  letter-spacing: 0.05em;
  line-height: 1.6;
  box-sizing: border-box;
  border-bottom: 2px solid #e6a23c;
  margin: 0 auto;
  overflow: hidden;
  /* 隐藏滚动条 */
  resize: none;

  position: absolute;
  bottom: 0;
  left: 0;

  width: 100vw;
  height: 16vw;
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

.bg {
  width: 100vw;
  display: block;
}
</style>