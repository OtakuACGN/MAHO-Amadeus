<template>
  <div class="character-stage" ref="stageContainer"></div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useStageStore } from '@/stores/modules/stage'
import { useAudioStore } from '@/stores/modules/audio'
import { storeToRefs } from 'pinia'
import { StageManager } from './core/StageManager'

const stageStore = useStageStore()
const audioStore = useAudioStore()
const { characters, background } = storeToRefs(stageStore)
const { mouthOpen, speakingCharacterId } = storeToRefs(audioStore)

const stageContainer = ref(null)
let stageManager = null

onMounted(async () => {
  // 1. 初始化管理器
  stageManager = new StageManager({
    backgroundAlpha: 0,
    resizeTo: window,
    resolution: window.devicePixelRatio || 1,
    autoDensity: true,
  })

  if (stageContainer.value) {
    stageContainer.value.appendChild(stageManager.app.view)
  }

  // 2. 加载 Live2D 运行库
  await stageManager.initLive2D()

  // 3. 监听变化并触发初始同步 (immediate: true 替代了 syncAll)
  watch(characters, (configs) => {
    if (stageManager) {
      stageManager.characterLayer.syncCharacters(
        configs, 
        stageManager.Live2DModel, 
        stageManager.screen
      )
    }
  }, { deep: true, immediate: true })

  watch(background, (bgConfig) => {
    if (stageManager) {
      stageManager.backgroundLayer.syncBackground(
        bgConfig, 
        stageManager.screen
      )
    }
  }, { deep: true, immediate: true })

  // 监听口型数值同步到 Live2D
  watch(mouthOpen, (val) => {
    if (stageManager) {
      stageManager.characterLayer.updateLipSync(speakingCharacterId.value, val)
    }
  })

  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (stageManager) {
    stageManager.destroy()
  }
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  if (stageManager) {
    stageManager.resize()
  }
}
</script>

<style scoped>
.character-stage {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: #000;
}
</style>