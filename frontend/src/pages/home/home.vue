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
    <!-- 注意DialogBox直接引用了useGameStore，因为这样子的话，可以避免很多父子传递的问题 -->
    <DialogBox class="dialog" />
    <SiriWave :visible="app.showSiriWave" class="Siri-wave"/>
    <CharacterStage class="stage" />
  </div>
</template>

<script setup>
import CharacterStage from '@/component/character/CharacterStage.vue'
import DialogBox from './DialogBox.vue'
import SiriWave from '@/component/DialogBox/SiriWave.vue'
import { onMounted } from 'vue'
import { useGameStore } from '@/stores/game'
import { useVADStore } from '@/stores/vad'
import { storeToRefs } from 'pinia'
import { useLipSyncAudio } from '@/composables/useLipSyncAudio'

const gameStore = useGameStore()
const vadStore = useVADStore()

// 使用拆分后的 Store 引用
const { app, ws, audio } = gameStore
const { wsStatus } = storeToRefs(ws)
const { buttonStates } = storeToRefs(app)
const { audioQueue } = storeToRefs(audio)

const { getAudioContext } = vadStore

const { processAudioQueue } = useLipSyncAudio(
  audioQueue,
  getAudioContext,
  (value) => {
    audio.mouthOpen = value
  }
)

onMounted(() => {
  vadStore.initVAD()
  vadStore.onVoiceStart = () => {
    if (buttonStates.value.video) {
      app.showDialog = false
      app.showSiriWave = true
    }
  }
  vadStore.onVoiceEnd = () => {
    if (buttonStates.value.video) {
      app.showDialog = true
      app.showSiriWave = false
    }
  }
  processAudioQueue()
})
</script>

<style scoped>
.stage {
  position: absolute;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1;
}

.home-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
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
  font-size: 2.1em;
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

.Siri-wave {
  position: absolute;
  bottom: 10vh;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
}
</style>