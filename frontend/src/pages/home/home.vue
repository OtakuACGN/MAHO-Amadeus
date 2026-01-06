<template>
  <div class="home-page">
    <div v-if="wsStatus !== 'connected'" class="ws-status-tip">WebSocket连接失效，正在尝试连接...</div>
    <!-- 左上角按钮区 -->
    <div class="button-sidebar">
      <div class="side-button" :class="{ active: buttonStates.video }" @click="buttonStates.video = !buttonStates.video"
        title="视频通话">
        <img src="@/assets/videocall.png" alt="video" />
      </div>
      <!-- 可以在这里继续添加更多按钮 -->
    </div>
    <dialogBox 
      class="dialog" 
      :currentName="currentName"
      :videoMode="buttonStates.video"
      :thinkText="thinkText"
      :isInputMode="!isWaiting"
      :textQueue="textQueue"
      @send="send"
    />
    <illustration class="illustrat" />
  </div>
</template>

<script setup>
import illustration from './illustration.vue'
import dialogBox from '@/component/DialogBox/index.vue'
import { onMounted } from 'vue'
import { useHomeStore } from '@/stores/home'
import { useVADStore } from '@/stores/vad'
import { storeToRefs } from 'pinia'
import { useLipSyncAudio } from '@/composables/useLipSyncAudio'

const homeStore = useHomeStore()
const vadStore = useVADStore()
const { audioQueue, wsStatus, buttonStates, textQueue, thinkText, isWaiting, currentName } = storeToRefs(homeStore)
const { send } = homeStore
const { getAudioContext } = vadStore

const { processAudioQueue } = useLipSyncAudio(
  audioQueue,
  getAudioContext,
  (value) => {
    homeStore.mouthOpen = value
  }
)

onMounted(() => {
  processAudioQueue()
})
</script>

<style scoped>
.illustrat {
  position: absolute;
}

.home-page {
  background-image: url('/bg.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  min-height: 100vh;
  position: relative;
}

.button-sidebar {
  position: absolute;
  top: 50px;
  /* 避开顶部的状态提示 */
  left: 2.8vw;
  display: flex;
  flex-direction: column;
  gap: 20px;
  z-index: 100;
}

.side-button {
  width: 64px;
  height: 64px;
  min-width: 40px;
  min-height: 40px;
  cursor: pointer;
  transition: all 0.3s ease;
  opacity: 0.8;
}

.side-button:active {
  transform: scale(0.95);
}

.side-button img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.side-button.active {
  opacity: 1;
}

.ws-status-tip {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  text-align: center;
  color: #e6a23c;
  font-family: 'Microsoft YaHei', 'SimHei', '黑体', 'STHeiti', sans-serif;
  font-size: 2.1vw;
  text-shadow: 2px 2px 6px #000, 0 0 1px #fff;
  padding: 0.5em 0;
  border: none;
  border-bottom: 2px solid #e6a23c;
  letter-spacing: 0.05em;
  line-height: 1.6;
  box-sizing: border-box;
  background: none;
  z-index: 10;
}

.dialog {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  z-index: 2;
}
</style>